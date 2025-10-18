# tests/test_data_loader.py
"""
Unit tests for the data_loader module.

These tests verify the data loading functionality for different file types:
- PDF processing (multi-modal vision approach)
- Audio transcription
- Video processing (audio extraction + transcription)
- Directory scanning and processing

All external API calls (Azure OpenAI) and system calls (FFmpeg) are mocked
to ensure tests are fast, reliable, and don't incur API costs.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch
from src.data_loader import (
    load_text_from_pdf,
    transcribe_audio_file,
    load_from_directory
)


def test_load_pdf_multimodal_successfully(mocker):
    """
    Tests the multi-modal PDF processing pipeline by mocking
    pdf-to-image conversion and the Vision Language Model API call.

    This test verifies:
    1. PDF pages are converted to images
    2. Each image is sent to the Vision API
    3. Text descriptions are collected and combined
    """
    fixture_path = Path(__file__).parent / "fixtures" / "sample.pdf"

    # Mock 1: pdf2image.convert_from_path returns fake PIL Image objects
    # We simulate a 2-page PDF
    mock_image = MagicMock()
    mocker.patch(
        "src.data_loader.convert_from_path",
        return_value=[mock_image, mock_image]
    )

    # Mock 2: The Vision Language Model API response
    # Create a mock that matches the structure: response.choices[0].message.content
    mock_message = MagicMock()
    mock_message.content = "This is a description of a page."

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_vlm_response = MagicMock()
    mock_vlm_response.choices = [mock_choice]

    # Mock 3: The Azure OpenAI client
    mock_client_instance = MagicMock()
    mock_client_instance.chat.completions.create.return_value = mock_vlm_response

    mocker.patch("src.data_loader.AzureOpenAI", return_value=mock_client_instance)

    # Call the function under test
    extracted_text = load_text_from_pdf(fixture_path)

    # Assertions
    # Should call the Vision API once per page (2 pages)
    assert mock_client_instance.chat.completions.create.call_count == 2

    # The extracted text should be the descriptions joined by double newlines
    expected_text = "This is a description of a page.\n\nThis is a description of a page."
    assert extracted_text == expected_text


def test_load_pdf_file_not_found():
    """
    Tests that a non-existent PDF file returns an empty string gracefully.
    """
    result = load_text_from_pdf("non_existent_file.pdf")
    assert result == ""


def test_transcribe_audio_file_mocked(mocker):
    """
    Tests the audio transcription function with a mocked Azure OpenAI client.
    Ensures the function correctly processes the Whisper API response without
    making a real call.
    """
    # Create test fixture path (the file doesn't need to actually exist due to mocking)
    fixture_path = Path(__file__).parent / "fixtures" / "sample.wav"

    # Mock 1: The Whisper API response
    mock_api_response = MagicMock()
    mock_api_response.text = "This is a test transcription."

    # Mock 2: The Azure OpenAI client
    mock_client_instance = MagicMock()
    mock_client_instance.audio.transcriptions.create.return_value = mock_api_response

    mocker.patch("src.data_loader.AzureOpenAI", return_value=mock_client_instance)

    # Mock 3: File existence check and file open
    mocker.patch.object(Path, 'is_file', return_value=True)
    mock_file_open = mocker.patch("builtins.open", mock_open(read_data=b"fake audio data"))

    # Call the function under test
    result_text = transcribe_audio_file(fixture_path)

    # Assertions
    # Verify the function returned the text from our mock response
    assert result_text == "This is a test transcription."

    # Verify the API client was called correctly
    mock_client_instance.audio.transcriptions.create.assert_called_once()

    # Verify the call included the correct model name
    call_kwargs = mock_client_instance.audio.transcriptions.create.call_args[1]
    assert call_kwargs["model"] == "whisper"


def test_transcribe_audio_file_not_found():
    """
    Tests that a ValueError is raised if the audio file doesn't exist.
    """
    with pytest.raises(ValueError, match="Audio file not found"):
        transcribe_audio_file("non_existent_audio.wav")


def test_load_from_directory_handles_pdf(mocker):
    """
    Tests that the directory loader correctly identifies and processes PDF files.
    """
    fixture_dir = Path(__file__).parent / "fixtures"

    # Mock the PDF loader to return fake content
    mock_pdf_content = "Text from PDF."
    mocker.patch(
        "src.data_loader.load_text_from_pdf",
        return_value=mock_pdf_content
    )

    # Mock audio and video loaders to return None (simulating no audio/video files)
    mocker.patch("src.data_loader.transcribe_audio_file", return_value=None)

    # Mock directory iteration to return only a PDF file
    mock_pdf_file = MagicMock(spec=Path)
    mock_pdf_file.is_file.return_value = True
    mock_pdf_file.suffix = ".pdf"
    mock_pdf_file.name = "sample.pdf"

    mocker.patch.object(
        Path,
        'iterdir',
        return_value=[mock_pdf_file]
    )

    # Also need to mock is_dir to return True for the directory
    mocker.patch.object(Path, 'is_dir', return_value=True)

    # Call the function under test
    documents = load_from_directory(fixture_dir)

    # Assertions
    assert len(documents) == 1
    assert documents[0]["source"] == "sample.pdf"
    assert documents[0]["content"] == "Text from PDF."


def test_load_from_directory_handles_audio(mocker):
    """
    Tests that the directory loader correctly identifies and processes audio files.
    """
    fixture_dir = Path(__file__).parent / "fixtures"

    # Mock the audio transcriber to return fake content
    mock_audio_content = "Text from audio."
    mocker.patch(
        "src.data_loader.transcribe_audio_file",
        return_value=mock_audio_content
    )

    # Mock PDF loader to return None
    mocker.patch("src.data_loader.load_text_from_pdf", return_value=None)

    # Mock directory iteration to return only an audio file
    mock_audio_file = MagicMock(spec=Path)
    mock_audio_file.is_file.return_value = True
    mock_audio_file.suffix = ".mp3"
    mock_audio_file.name = "sample.mp3"

    mocker.patch.object(
        Path,
        'iterdir',
        return_value=[mock_audio_file]
    )

    mocker.patch.object(Path, 'is_dir', return_value=True)

    # Call the function under test
    documents = load_from_directory(fixture_dir)

    # Assertions
    assert len(documents) == 1
    assert documents[0]["source"] == "sample.mp3"
    assert documents[0]["content"] == "Text from audio."


def test_load_from_directory_handles_mp4(mocker):
    """
    Tests that the directory loader correctly handles MP4 video files
    by mocking the audio extraction and transcription process.

    This verifies the complete workflow:
    1. MP4 file detected
    2. Audio extracted with FFmpeg
    3. Extracted audio transcribed
    """
    fixture_dir = Path(__file__).parent / "fixtures"

    # Mock 1: FFmpeg audio extraction
    # We need to mock the entire ffmpeg chain: input().output().run()
    mock_ffmpeg_input = MagicMock()
    mock_ffmpeg_output = MagicMock()
    mock_ffmpeg_run = MagicMock()

    mock_ffmpeg_output.run = mock_ffmpeg_run
    mock_ffmpeg_input.output = MagicMock(return_value=mock_ffmpeg_output)

    mocker.patch("src.data_loader.ffmpeg.input", return_value=mock_ffmpeg_input)

    # Mock 2: Audio transcriber
    mock_transcription = "Text from video."
    mocker.patch(
        "src.data_loader.transcribe_audio_file",
        return_value=mock_transcription
    )

    # Mock 3: PDF loader to return None
    mocker.patch("src.data_loader.load_text_from_pdf", return_value=None)

    # Mock 4: Directory iteration to return only an MP4 file
    mock_mp4_file = MagicMock(spec=Path)
    mock_mp4_file.is_file.return_value = True
    mock_mp4_file.suffix = ".mp4"
    mock_mp4_file.name = "sample.mp4"
    mock_mp4_file.__str__ = lambda self: "sample.mp4"

    mocker.patch.object(
        Path,
        'iterdir',
        return_value=[mock_mp4_file]
    )

    mocker.patch.object(Path, 'is_dir', return_value=True)

    # Call the function under test
    documents = load_from_directory(fixture_dir)

    # Assertions
    # Verify we got the MP4 document
    mp4_doc = next((doc for doc in documents if doc["source"] == "sample.mp4"), None)
    assert mp4_doc is not None, "MP4 document was not processed"
    assert mp4_doc["content"] == "Text from video."

    # Verify FFmpeg was called to extract audio
    mock_ffmpeg_run.assert_called_once()


def test_load_from_directory_mixed_files(mocker):
    """
    Integration test: Verify the directory loader can handle a mix of
    PDF, audio, and video files in a single directory.
    """
    fixture_dir = Path(__file__).parent / "fixtures"

    # Mock all the file processors
    mocker.patch("src.data_loader.load_text_from_pdf", return_value="PDF content")
    mocker.patch("src.data_loader.transcribe_audio_file", return_value="Audio content")

    # Mock FFmpeg for video processing
    mock_ffmpeg_input = MagicMock()
    mock_ffmpeg_output = MagicMock()
    mock_ffmpeg_output.run = MagicMock()
    mock_ffmpeg_input.output = MagicMock(return_value=mock_ffmpeg_output)
    mocker.patch("src.data_loader.ffmpeg.input", return_value=mock_ffmpeg_input)

    # Create mock files of different types
    mock_pdf = MagicMock(spec=Path)
    mock_pdf.is_file.return_value = True
    mock_pdf.suffix = ".pdf"
    mock_pdf.name = "document.pdf"

    mock_audio = MagicMock(spec=Path)
    mock_audio.is_file.return_value = True
    mock_audio.suffix = ".mp3"
    mock_audio.name = "audio.mp3"

    mock_video = MagicMock(spec=Path)
    mock_video.is_file.return_value = True
    mock_video.suffix = ".mp4"
    mock_video.name = "video.mp4"
    mock_video.__str__ = lambda self: "video.mp4"

    mocker.patch.object(
        Path,
        'iterdir',
        return_value=[mock_pdf, mock_audio, mock_video]
    )

    mocker.patch.object(Path, 'is_dir', return_value=True)

    # Call the function under test
    documents = load_from_directory(fixture_dir)

    # Assertions
    # Should have processed all 3 files
    assert len(documents) == 3

    # Verify we have one of each type
    sources = {doc["source"] for doc in documents}
    assert "document.pdf" in sources
    assert "audio.mp3" in sources
    assert "video.mp4" in sources
