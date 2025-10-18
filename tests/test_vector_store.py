# tests/test_vector_store.py
"""
Unit tests for the vector_store module.

These tests verify the vector database functionality:
- Database initialization and persistence
- Embedding generation and storage
- Integration between embeddings and ChromaDB

All Azure OpenAI API calls are mocked to ensure tests are fast and free.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock
import chromadb
from src.vector_store import get_vector_database_collection, embed_and_store_chunks


def test_db_initialization(tmp_path):
    """
    Tests that the ChromaDB client is initialized correctly in a temporary directory.

    Uses pytest's tmp_path fixture to create an isolated temporary directory
    that is automatically cleaned up after the test.

    Verifies:
    - Collection is created
    - Collection has the correct name
    - Database directory is created on disk
    """
    # Define a database path within the temporary directory
    db_test_path = str(tmp_path / "test_db")
    test_collection_name = "test_collection"

    # Call the function under test
    collection = get_vector_database_collection(
        db_path=db_test_path,
        collection_name=test_collection_name
    )

    # Assertions
    # Check that the returned object is a ChromaDB Collection
    assert isinstance(collection, chromadb.Collection)

    # Check that the collection has the correct name
    assert collection.name == test_collection_name

    # Check that the database directory was physically created
    assert (tmp_path / "test_db").exists()
    assert (tmp_path / "test_db").is_dir()


def test_db_get_or_create_idempotent(tmp_path):
    """
    Tests that calling get_vector_database_collection multiple times
    returns the same collection (idempotent behavior).
    """
    db_test_path = str(tmp_path / "test_db")
    test_collection_name = "test_collection"

    # Call the function twice
    collection1 = get_vector_database_collection(db_test_path, test_collection_name)
    collection2 = get_vector_database_collection(db_test_path, test_collection_name)

    # Both should return the same collection
    assert collection1.name == collection2.name == test_collection_name


def test_embedding_and_storing(mocker, tmp_path):
    """
    Tests the embedding and storing pipeline with a mocked Azure OpenAI client.

    This is a critical integration test that verifies:
    1. Embeddings are requested from Azure OpenAI
    2. The API response is correctly parsed
    3. Data is stored in ChromaDB with proper structure
    4. Metadata is preserved
    """
    # Setup: Create a temporary database and collection
    db_test_path = str(tmp_path / "test_db")
    collection = get_vector_database_collection(db_path=db_test_path)

    # Sample chunks to embed
    sample_chunks = [
        {"source": "doc1.pdf", "content": "This is the first chunk."},
        {"source": "doc2.txt", "content": "This is the second chunk."},
    ]

    # Mocking: Create fake embeddings response from Azure OpenAI
    # The API returns an object with a .data attribute containing Embedding objects
    # Each Embedding object has an .embedding attribute (list of floats)

    # Create mock Embedding objects
    mock_embedding_1 = MagicMock()
    mock_embedding_1.embedding = [0.1] * 1536  # Simulating text-embedding-ada-002's dimension

    mock_embedding_2 = MagicMock()
    mock_embedding_2.embedding = [0.2] * 1536

    # Create mock API response with .data attribute
    mock_api_response = MagicMock()
    mock_api_response.data = [mock_embedding_1, mock_embedding_2]

    # Patch the AzureOpenAI client and its embeddings.create method
    mock_client_instance = MagicMock()
    mock_client_instance.embeddings.create.return_value = mock_api_response
    mocker.patch("src.vector_store.AzureOpenAI", return_value=mock_client_instance)

    # Call the function under test
    embed_and_store_chunks(chunks=sample_chunks, collection=collection)

    # Assertions

    # 1. Verify the embedding API was called correctly
    mock_client_instance.embeddings.create.assert_called_once()
    call_kwargs = mock_client_instance.embeddings.create.call_args[1]

    # Check that all chunk contents were sent for embedding
    assert call_kwargs["input"] == [
        "This is the first chunk.",
        "This is the second chunk."
    ]

    # Check that the correct model was specified
    assert call_kwargs["model"] == "text-embedding-ada-002"

    # 2. Verify data was stored in ChromaDB
    # Check the count of items in the collection
    assert collection.count() == 2

    # 3. Retrieve the stored items and verify their structure
    stored_items = collection.get(include=["metadatas", "documents"])

    # Check IDs
    assert sorted(stored_items["ids"]) == ["chunk_0", "chunk_1"]

    # Check documents (the actual text content)
    assert "This is the first chunk." in stored_items["documents"]
    assert "This is the second chunk." in stored_items["documents"]

    # Check metadatas (source information)
    assert {"source": "doc1.pdf"} in stored_items["metadatas"]
    assert {"source": "doc2.txt"} in stored_items["metadatas"]


def test_embedding_empty_chunks(tmp_path):
    """
    Tests that embed_and_store_chunks handles an empty list gracefully.
    """
    db_test_path = str(tmp_path / "test_db")
    collection = get_vector_database_collection(db_path=db_test_path)

    # Call with empty list
    embed_and_store_chunks(chunks=[], collection=collection)

    # Should not crash, and collection should remain empty
    assert collection.count() == 0


def test_embedding_single_chunk(mocker, tmp_path):
    """
    Tests embedding and storing a single chunk (edge case).
    """
    db_test_path = str(tmp_path / "test_db")
    collection = get_vector_database_collection(db_path=db_test_path)

    single_chunk = [{"source": "single.txt", "content": "Just one chunk."}]

    # Mock the embedding API
    mock_embedding = MagicMock()
    mock_embedding.embedding = [0.5] * 1536

    mock_api_response = MagicMock()
    mock_api_response.data = [mock_embedding]

    mock_client_instance = MagicMock()
    mock_client_instance.embeddings.create.return_value = mock_api_response
    mocker.patch("src.vector_store.AzureOpenAI", return_value=mock_client_instance)

    # Call the function
    embed_and_store_chunks(chunks=single_chunk, collection=collection)

    # Verify
    assert collection.count() == 1
    stored_items = collection.get()
    assert stored_items["documents"][0] == "Just one chunk."
