# src/data_loader.py
"""
Data Loading Module for RAG Chatbot

This module handles loading and processing data from various file formats:
- PDFs: Converted to images and processed with Vision Language Models
- Audio files: Transcribed using Azure OpenAI Whisper
- Video files (MP4): Audio extracted then transcribed

The module uses a multi-modal approach for PDFs, which is more robust than
traditional text extraction and can handle complex layouts, tables, and figures.

Key Features:
- Multi-modal PDF processing (PDF → Images → VLM → Text)
- Audio transcription (direct audio files)
- Video transcription (extract audio from MP4, then transcribe)
- Directory-based batch processing
"""

import base64
import tempfile
import time
from io import BytesIO
from pathlib import Path
from typing import Union, List

# PDF processing imports
from pdf2image import convert_from_path
import pypdf

# FFmpeg for video processing
import ffmpeg

# Progress bar
from tqdm import tqdm

# Azure OpenAI client for vision and transcription
from openai import AzureOpenAI
from openai import RateLimitError

# Azure Document Intelligence for PDF processing
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

# Configuration
from src.config import settings


def load_text_from_pdf(file_path: Union[str, Path], method: str = "document_intelligence") -> str:
    """
    Processes a PDF by extracting text.

    Three methods available:
    1. "document_intelligence" (DEFAULT): Azure Document Intelligence - BEST for any PDF
       - Handles text, images, tables, layouts
       - Fast, accurate, cost-effective
       - Separate rate limits from OpenAI
    2. "text_extraction": PyPDF text extraction - FREE but only works for text PDFs
    3. "vision": OpenAI Vision API - EXPENSIVE and slow, has strict rate limits

    Args:
        file_path: Path to the PDF file to process
        method: Processing method ("document_intelligence", "text_extraction", or "vision")

    Returns:
        str: Extracted or generated text from the PDF

    Raises:
        Exception: If processing fails (errors are logged)
    """
    # Normalize file path
    if not isinstance(file_path, Path):
        file_path = Path(file_path)

    # Validate file exists and is a PDF
    if not file_path.exists():
        print(f"Error: PDF file not found: {file_path}")
        return ""

    if file_path.suffix.lower() != ".pdf":
        print(f"Error: File is not a PDF: {file_path}")
        return ""

    # Route to appropriate processor
    if method == "document_intelligence":
        return _process_pdf_with_document_intelligence(file_path)
    elif method == "text_extraction":
        return _extract_text_from_pdf(file_path)
    elif method == "vision":
        return _process_pdf_with_vision(file_path)
    else:
        print(f"Error: Unknown method '{method}'")
        return ""


def _process_pdf_with_document_intelligence(file_path: Path) -> str:
    """
    Process PDF using Azure Document Intelligence (RECOMMENDED).

    This is the best option for PDF processing:
    - Works with any PDF (text, images, scanned documents)
    - Extracts tables, layouts, structure
    - Fast and cost-effective
    - Separate rate limits from OpenAI
    - Built specifically for document processing

    Cost: ~$0.001 per page (much cheaper than Vision API!)
    Time: ~1-2 seconds per page

    Args:
        file_path: Path to PDF file

    Returns:
        str: Extracted text from all pages with layout preserved
    """
    try:
        print(f"📄 Processing '{file_path.name}' with Azure Document Intelligence...")

        # Initialize Document Intelligence client
        # Using same endpoint and key as Azure OpenAI (AIServices resource includes both)
        client = DocumentAnalysisClient(
            endpoint=settings.azure_openai_endpoint,
            credential=AzureKeyCredential(settings.azure_openai_api_key)
        )

        # Open and analyze the PDF
        with open(file_path, "rb") as pdf_file:
            poller = client.begin_analyze_document(
                "prebuilt-read",  # Prebuilt model for reading documents
                document=pdf_file
            )
            result = poller.result()

        # Extract text from all pages
        all_pages_text = []

        print(f"   Analyzing {len(result.pages)} pages...")

        for page_num, page in enumerate(tqdm(result.pages, desc="Analyzing", unit="page"), 1):
            # Extract lines of text from this page
            page_text_lines = []

            # Get lines in reading order
            for line in page.lines:
                page_text_lines.append(line.content)

            # Join lines for this page
            page_text = "\n".join(page_text_lines)

            if page_text.strip():
                # Add page marker for reference
                all_pages_text.append(f"--- Page {page_num} ---\n{page_text}")

        combined_text = "\n\n".join(all_pages_text)

        print(f"✅ Extracted {len(combined_text)} characters from {len(result.pages)} pages")

        return combined_text

    except Exception as e:
        print(f"❌ Error with Document Intelligence: {e}")
        print(f"   Falling back to simple text extraction...")
        return _extract_text_from_pdf(file_path)


def _extract_text_from_pdf(file_path: Path) -> str:
    """
    Extract text directly from PDF using pypdf (FREE and INSTANT).

    This works great for:
    - Text-heavy PDFs (presentations, documents, papers)
    - PDFs with embedded text (not scanned images)

    This doesn't work for:
    - Scanned documents (images of text)
    - Complex charts/diagrams that need description

    Args:
        file_path: Path to PDF file

    Returns:
        str: Extracted text from all pages
    """
    try:
        print(f"📄 Extracting text from '{file_path.name}' (FREE - using PyPDF)...")

        reader = pypdf.PdfReader(str(file_path))
        all_text = []

        for page_num, page in enumerate(tqdm(reader.pages, desc="Extracting", unit="page"), 1):
            text = page.extract_text()
            if text.strip():
                all_text.append(text)

        print(f"✅ Extracted text from {len(all_text)}/{len(reader.pages)} pages")
        return "\n\n".join(all_text)

    except Exception as e:
        print(f"❌ Error extracting text from PDF: {e}")
        print(f"   Try with use_vision=True for image-based PDFs")
        return ""


def _process_pdf_with_vision(file_path: Path) -> str:
    """
    Process PDF using Vision API (EXPENSIVE but handles images).

    Cost: ~$0.03 per page
    Time: ~2-3 seconds per page
    Rate limits: Will auto-retry with backoff

    Args:
        file_path: Path to PDF file

    Returns:
        str: AI-generated descriptions of each page
    """
    # Step 1: Convert PDF pages to images
    try:
        print(f"📄 Converting PDF '{file_path.name}' to images...")
        images = convert_from_path(str(file_path))
        print(f"✅ Converted {len(images)} pages to images")
    except Exception as e:
        print(f"❌ Error converting PDF to images: {e}")
        return ""

    # Step 2: Initialize Azure OpenAI client for vision processing
    client = AzureOpenAI(
        api_key=settings.azure_openai_api_key,
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.openai_api_version,
    )

    # Step 3: Process each page image with the Vision Language Model
    all_page_descriptions = []

    print(f"\n⏳ Processing {len(images)} pages with Vision API...")
    print(f"   Cost: ~${len(images) * 0.03:.2f}  |  Time: ~{len(images) * 2}-{len(images) * 3} seconds")
    print(f"   Note: Will auto-retry on rate limits with delays\n")

    for i, image in enumerate(tqdm(images, desc="Vision API", unit="page")):
        # Convert PIL Image to base64 string for API transmission
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # Retry logic for rate limits
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Call Vision API with multi-modal message
                response = client.chat.completions.create(
                    model=settings.llm_model_name,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        "Describe the content of this page from a document. "
                                        "Include all text, titles, headings, and describe any "
                                        "figures, charts, tables, or diagrams. Be comprehensive "
                                        "and preserve the structure of the information."
                                    )
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{img_base64}"
                                    },
                                },
                            ],
                        }
                    ],
                    max_tokens=2048,
                )

                # Extract the text description from the response
                description = response.choices[0].message.content
                if description:
                    all_page_descriptions.append(description)

                # Add delay to respect rate limits (10k tokens/min)
                # Vision API ~1500 tokens/page = 6-7 pages/min = 6s between pages
                time.sleep(6)
                break  # Success, exit retry loop

            except RateLimitError as e:
                if attempt < max_retries - 1:
                    wait_time = 60  # Wait full 60 seconds as API suggests
                    tqdm.write(f"⚠️  Rate limit hit, waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    tqdm.write(f"❌ Failed page {i+1} after {max_retries} attempts")

            except Exception as e:
                tqdm.write(f"⚠️  Error on page {i+1}: {str(e)[:100]}")
                break  # Don't retry on other errors

    print(f"\n✅ Successfully processed {len(all_page_descriptions)}/{len(images)} pages")

    # Combine all page descriptions with clear separation
    return "\n\n".join(all_page_descriptions)


def transcribe_audio_file(file_path: Union[str, Path]) -> str:
    """
    Transcribes an audio file using Azure OpenAI's Whisper model.

    Whisper is a state-of-the-art speech recognition model that supports
    multiple languages and handles various audio qualities well.

    Args:
        file_path: Path to the audio file (.wav, .mp3, .m4a, etc.)

    Returns:
        str: Transcribed text from the audio file

    Raises:
        Exception: If transcription fails (errors are logged)
    """
    # Normalize file path
    if not isinstance(file_path, Path):
        file_path = Path(file_path)

    # Validate file exists
    if not file_path.is_file():
        raise ValueError(f"Audio file not found at: {file_path}")

    try:
        print(f"Transcribing audio file: {file_path.name}...")

        # Initialize Azure OpenAI client
        client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.openai_api_version,
        )

        # Open the audio file and send for transcription
        # Whisper model name is typically just "whisper" in Azure
        with open(file_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="whisper",  # Azure OpenAI Whisper deployment
                file=audio_file
            )

        print(f"✓ Audio transcription complete: {file_path.name}")
        return result.text

    except Exception as e:
        print(f"Error during audio transcription for {file_path}: {e}")
        return ""


def load_from_directory(directory_path: Union[str, Path]) -> List[dict]:
    """
    Loads all supported documents from a directory into a standardized list.

    This is the main entry point for the data loading pipeline. It scans a directory,
    identifies supported file types, and processes each appropriately:
    - PDFs: Multi-modal vision processing
    - Audio (.wav, .mp3, .m4a): Direct transcription
    - Video (.mp4): Extract audio, then transcribe

    The function returns a consistent data structure regardless of input file type,
    making it easy for downstream processing (chunking, embedding) to work uniformly.

    Args:
        directory_path: Path to directory containing knowledge base files

    Returns:
        List[dict]: List of documents, each with 'source' (filename) and 'content' (text)

    Example:
        [
            {'source': 'lecture.pdf', 'content': 'Text from PDF...'},
            {'source': 'audio.mp3', 'content': 'Transcribed audio...'},
        ]

    Raises:
        ValueError: If directory_path is not a valid directory
    """
    # Normalize directory path
    if not isinstance(directory_path, Path):
        directory_path = Path(directory_path)

    # Validate directory exists
    if not directory_path.is_dir():
        raise ValueError(f"Provided path is not a valid directory: {directory_path}")

    # Initialize results list
    documents = []

    # Define supported file extensions
    supported_audio = {".wav", ".mp3", ".m4a"}
    supported_video = {".mp4"}

    print(f"\nScanning directory: {directory_path}")
    print(f"Looking for PDFs, audio files {supported_audio}, and video files {supported_video}")

    # Iterate through all files in the directory
    for file_path in directory_path.iterdir():
        # Skip directories
        if not file_path.is_file():
            continue

        doc = None
        file_ext = file_path.suffix.lower()

        # Process PDF files
        if file_ext == ".pdf":
            print(f"\n📄 Found PDF: {file_path.name}")
            content = load_text_from_pdf(file_path)
            if content:
                doc = {"source": file_path.name, "content": content}

        # Process audio files
        elif file_ext in supported_audio:
            print(f"\n🎵 Found audio file: {file_path.name}")
            content = transcribe_audio_file(file_path)
            if content:
                doc = {"source": file_path.name, "content": content}

        # Process video files (MP4)
        elif file_ext in supported_video:
            print(f"\n🎬 Found video file: {file_path.name}")

            # Use a temporary file for the extracted audio
            # delete=True ensures cleanup even if an error occurs
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as tmp_audio_file:
                try:
                    print(f"Extracting audio from {file_path.name}...")

                    # Use FFmpeg to extract audio track and convert to MP3
                    # Compress to stay under Whisper's 25MB limit
                    # - acodec='libmp3lame': MP3 codec
                    # - audio_bitrate='64k': Compress audio (lower quality but smaller)
                    # - ar='16000': Downsample to 16kHz (Whisper's native rate)
                    # - ac=1: Mono (Whisper doesn't need stereo)
                    (
                        ffmpeg
                        .input(str(file_path))
                        .output(
                            tmp_audio_file.name,
                            acodec='libmp3lame',
                            audio_bitrate='64k',  # Compress to stay under 25MB
                            ar='16000',           # 16kHz sample rate
                            ac=1                   # Mono
                        )
                        .run(overwrite_output=True, quiet=True)
                    )

                    print(f"✓ Audio extracted successfully")

                    # Transcribe the extracted audio
                    content = transcribe_audio_file(tmp_audio_file.name)
                    if content:
                        doc = {"source": file_path.name, "content": content}

                except ffmpeg.Error as e:
                    # FFmpeg errors include stderr which is helpful for debugging
                    error_msg = e.stderr.decode() if e.stderr else str(e)
                    print(f"Error extracting audio from {file_path.name}: {error_msg}")

        # Add document to results if processing was successful
        if doc:
            documents.append(doc)
            print(f"✓ Successfully processed: {file_path.name}")

    print(f"\n✅ Directory scan complete: {len(documents)} documents loaded")
    return documents
