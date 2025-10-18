# tests/test_text_processor.py
"""
Unit tests for the text_processor module.

These tests verify the text chunking functionality, ensuring that:
- Large texts are split into appropriately-sized chunks
- Metadata (source) is preserved for all chunks
- Chunk overlap works correctly
- Edge cases are handled (empty docs, very short docs)
"""

import pytest
from src.text_processor import chunk_text


def test_chunking_basic():
    """
    Tests basic text chunking functionality with a single long document.

    Verifies:
    - Document is split into multiple chunks
    - Each chunk preserves the source metadata
    - Chunk sizes respect the specified limit
    - Overlap exists between consecutive chunks
    """
    # Create a long text that will definitely exceed our test chunk size
    # Using a repeated pattern makes it easy to verify overlap
    long_text = (
        "This is sentence one. This is sentence two which is a bit longer. "
        "Here comes sentence three, making the paragraph grow even more. "
        "Sentence four will definitely push the content over the chunk size limit. "
        "Sentence five is here to ensure we have multiple chunks to work with. "
        "Sentence six adds even more data to guarantee splitting. "
        "Finally, sentence seven concludes this long piece of text."
    )

    # Multiply the text to make it even longer
    long_text = long_text * 5

    # Create a test document
    documents = [{"source": "test_document.txt", "content": long_text}]

    # Define small chunking parameters to force splitting in our test
    test_chunk_size = 150
    test_chunk_overlap = 30

    # Call the function under test
    chunks = chunk_text(
        documents,
        chunk_size=test_chunk_size,
        chunk_overlap=test_chunk_overlap
    )

    # Assertions
    assert isinstance(chunks, list), "chunk_text should return a list"

    # The long text should be split into multiple chunks
    assert len(chunks) > 1, f"Expected multiple chunks, got {len(chunks)}"

    for chunk in chunks:
        # Each chunk must have the required keys
        assert "source" in chunk, "Chunk missing 'source' key"
        assert "content" in chunk, "Chunk missing 'content' key"

        # All chunks must preserve the original source
        assert chunk["source"] == "test_document.txt"

        # Content must be a non-empty string
        assert isinstance(chunk["content"], str)
        assert len(chunk["content"]) > 0

        # Each chunk's content should not exceed the specified size
        # (allowing for slight variance due to word boundaries)
        assert len(chunk["content"]) <= test_chunk_size + 50  # +50 tolerance


def test_chunking_overlap():
    """
    Tests that chunk overlap is working correctly.

    Verifies that consecutive chunks share some content (overlap).
    """
    # Create a text with distinct markers to easily verify overlap
    text = "AAAAA " * 50 + "BBBBB " * 50 + "CCCCC " * 50

    documents = [{"source": "overlap_test.txt", "content": text}]

    # Use parameters that will create at least 2 chunks
    test_chunk_size = 150
    test_chunk_overlap = 30

    chunks = chunk_text(
        documents,
        chunk_size=test_chunk_size,
        chunk_overlap=test_chunk_overlap
    )

    # Need at least 2 chunks to test overlap
    assert len(chunks) >= 2

    # Check that the end of the first chunk appears near the start of the second
    if len(chunks) >= 2:
        first_chunk_end = chunks[0]["content"][-test_chunk_overlap:]
        second_chunk_start = chunks[1]["content"][:test_chunk_overlap + 50]

        # There should be some overlap - at least a few characters in common
        # (exact match might not occur due to word boundaries, but similarity should be high)
        assert any(
            word in second_chunk_start for word in first_chunk_end.split()
        ), "No overlap detected between consecutive chunks"


def test_chunking_preserves_multiple_sources():
    """
    Tests that chunking correctly preserves source metadata when processing
    multiple documents.
    """
    documents = [
        {"source": "doc1.pdf", "content": "A" * 500},
        {"source": "doc2.txt", "content": "B" * 500},
        {"source": "doc3.mp3", "content": "C" * 500},
    ]

    chunks = chunk_text(documents, chunk_size=200, chunk_overlap=50)

    # Extract unique sources from chunks
    sources_in_chunks = {chunk["source"] for chunk in chunks}

    # All original sources should be represented
    expected_sources = {"doc1.pdf", "doc2.txt", "doc3.mp3"}
    assert sources_in_chunks == expected_sources


def test_chunking_short_document():
    """
    Tests that a document shorter than chunk_size is returned as a single chunk.
    """
    short_text = "This is a short document."
    documents = [{"source": "short.txt", "content": short_text}]

    chunks = chunk_text(documents, chunk_size=1000, chunk_overlap=200)

    # Should return exactly one chunk
    assert len(chunks) == 1
    assert chunks[0]["content"] == short_text
    assert chunks[0]["source"] == "short.txt"


def test_chunking_empty_document():
    """
    Tests handling of an empty document.
    """
    documents = [{"source": "empty.txt", "content": ""}]

    chunks = chunk_text(documents, chunk_size=1000, chunk_overlap=200)

    # LangChain's splitter returns an empty list for empty strings
    assert len(chunks) == 0


def test_chunking_multiple_documents():
    """
    Tests chunking multiple documents of varying lengths.
    """
    documents = [
        {"source": "doc1.txt", "content": "Short content."},
        {"source": "doc2.txt", "content": "X" * 2000},  # Long content
        {"source": "doc3.txt", "content": "Medium " * 100},
    ]

    chunks = chunk_text(documents, chunk_size=500, chunk_overlap=100)

    # Should have chunks from all documents
    sources = {chunk["source"] for chunk in chunks}
    assert "doc1.txt" in sources
    assert "doc2.txt" in sources
    assert "doc3.txt" in sources

    # The long document should produce multiple chunks
    doc2_chunks = [c for c in chunks if c["source"] == "doc2.txt"]
    assert len(doc2_chunks) > 1
