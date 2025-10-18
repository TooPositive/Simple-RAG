Spec Task DATA-1: Multi-Modal PDF Processor
🎯 Objective
To implement a function that processes a PDF by converting each page into an image and then using a multi-modal Vision Language Model (VLM) to generate a rich, textual description of the content on each page. This approach completely bypasses traditional OCR and works on any PDF, including scanned documents or presentations with complex layouts.

🔑 Key Components & Rationale
pdf2image library: A Python wrapper for the poppler utility, used to convert PDF pages into high-quality images.

Azure OpenAI Vision Model (GPT-4o or GPT-4 Turbo with Vision): This is the core of the new approach. It will take a page image as input and generate a detailed text description of its contents, including text, charts, and layout information.

New Workflow: The logic changes from PDF -> Extracted Text to PDF -> Page Images -> VLM -> Text Descriptions. This is a practical implementation of the "Treat Pages as Images" concept from your slides.

✅ Acceptance Criteria
The pdf2image library is added to requirements.txt.

The system dependency poppler is installed locally and added to the Dockerfile.

The load_text_from_pdf function in src/data_loader.py is completely replaced with the new multi-modal logic.

The test test_load_pdf_successfully in tests/test_data_loader.py is rewritten to mock both the PDF-to-image conversion and the VLM API call, verifying the new orchestration.

📝 Detailed Steps
1. Update Dependencies 🐍

Add the following to your requirements.txt file:

# PDF to Image Conversion
pdf2image
Install the library:

Bash

pip install -r requirements.txt
2. Install System Prerequisite: Poppler

For local development, pdf2image requires the poppler utility.

macOS: brew install poppler

Ubuntu/Debian: sudo apt update && sudo apt install poppler-utils

Windows: Requires downloading binaries and adding them to your PATH. Follow these instructions.

3. Update Dockerfile for Poppler 🐳

Add poppler-utils to your Dockerfile so it's available inside the container.

Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install system dependencies, including poppler for pdf2image and ffmpeg
RUN apt-get update && apt-get install -y ffmpeg poppler-utils

# ... (rest of Dockerfile)
4. Implement the New Multi-Modal PDF Loader

Replace the entire existing load_text_from_pdf function in src/data_loader.py with this new version.

Python

# src/data_loader.py (add new imports and replace the function)
import base64
from io import BytesIO
from pdf2image import convert_from_path
from openai import AzureOpenAI
from pathlib import Path
from src.config import settings

def load_text_from_pdf(file_path: str | Path) -> str:
    """
    Processes a PDF by converting each page to an image and using a VLM
    to generate a text description.
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)

    try:
        images = convert_from_path(str(file_path))
    except Exception as e:
        print(f"Error converting PDF to images for {file_path.name}: {e}")
        return ""

    client = AzureOpenAI(
        api_key=settings.azure_openai_api_key,
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.openai_api_version,
    )

    all_page_descriptions = []
    for i, image in enumerate(images):
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        try:
            print(f"Processing page {i+1}/{len(images)} of {file_path.name}...")
            response = client.chat.completions.create(
                model=settings.llm_model_name, # Use your GPT-4o or Vision-enabled model
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe the content of this page from a document. Include all text, titles, and describe any figures or charts."},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{img_base64}"},
                            },
                        ],
                    }
                ],
                max_tokens=2048,
            )
            description = response.choices[0].message.content
            if description:
                all_page_descriptions.append(description)
        except Exception as e:
            print(f"Error processing page {i+1} with VLM: {e}")

    return "\n\n".join(all_page_descriptions)
5. Rewrite the Unit Test 🧪

Replace the old PDF test(s) in tests/test_data_loader.py with this new version that mocks the external processes.

Python

# tests/test_data_loader.py (replace the old PDF test)
from unittest.mock import MagicMock
from pathlib import Path
from src.data_loader import load_text_from_pdf

def test_load_pdf_multimodal_successfully(mocker):
    """
    Tests the multi-modal PDF processing pipeline by mocking
    pdf-to-image conversion and the VLM API call.
    """
    fixture_path = Path(__file__).parent / "fixtures" / "sample.pdf"

    # 1. Mock pdf2image.convert_from_path to return fake image objects
    mock_image = MagicMock()
    mocker.patch("src.data_loader.convert_from_path", return_value=[mock_image, mock_image])

    # 2. Mock the VLM API response
    mock_vlm_response = MagicMock()
    mock_vlm_response.choices[0].message.content = "This is a description of a page."
    mock_client_instance = MagicMock()
    mock_client_instance.chat.completions.create.return_value = mock_vlm_response
    mocker.patch("src.data_loader.AzureOpenAI", return_value=mock_client_instance)

    # 3. Call the function under test
    extracted_text = load_text_from_pdf(fixture_path)

    # 4. Assertions
    assert mock_client_instance.chat.completions.create.call_count == 2
    assert extracted_text == "This is a description of a page.\n\nThis is a description of a page."
🧪 TDD - Verification
Navigate to the root rag-chatbot directory.

Run the test suite:

Bash

pytest
The output should show the new test_load_pdf_multimodal_successfully test passing. This confirms your new data loading logic is correct and properly isolated from external dependencies for testing.