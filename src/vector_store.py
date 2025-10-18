# src/vector_store.py
"""
Vector Store Module for RAG Chatbot

This module manages all interactions with the vector database (ChromaDB):
- Initializing persistent database connections
- Generating embeddings using Azure OpenAI
- Storing embeddings with metadata
- Querying for similar vectors

Vector databases are the heart of RAG systems. They allow us to:
1. Convert text into high-dimensional vectors (embeddings)
2. Store these vectors efficiently
3. Perform fast similarity searches to find relevant context

ChromaDB is used because it:
- Runs locally (no external service needed)
- Persists to disk
- Has a simple Python API
- Handles embeddings and metadata together
"""

from pathlib import Path
from typing import List, Dict
import hashlib
import warnings
import os
import sys
from contextlib import contextmanager

import chromadb
from chromadb.types import Collection
from openai import AzureOpenAI
from src.config import settings

# ChromaDB 0.4.22 has a telemetry bug that causes harmless warnings
# This context manager suppresses those specific warnings
@contextmanager
def suppress_chromadb_warnings():
    """Temporarily redirect stderr to suppress ChromaDB telemetry warnings."""
    stderr = sys.stderr
    sys.stderr = open(os.devnull, 'w')
    try:
        yield
    finally:
        sys.stderr.close()
        sys.stderr = stderr


def get_vector_database_collection(
    db_path: str = "./chroma_db",
    collection_name: str = "documents"
) -> Collection:
    """
    Initializes a persistent ChromaDB client and returns a collection.

    A "collection" in ChromaDB is similar to a table in a traditional database.
    It stores vectors, their associated text content, and metadata.

    Persistence is critical: The database is saved to disk in db_path,
    allowing the application to restart without re-processing all documents.

    Args:
        db_path: Path to directory where ChromaDB will store data
        collection_name: Name of the collection to create/load

    Returns:
        Collection: A ChromaDB Collection object for adding and querying vectors

    Note:
        get_or_create_collection ensures this function is idempotent:
        - First run: Creates the collection
        - Subsequent runs: Returns the existing collection
    """
    # Ensure the database directory exists
    db_path_obj = Path(db_path)
    if not db_path_obj.exists():
        print(f"Database path '{db_path}' not found, creating it...")
        db_path_obj.mkdir(parents=True, exist_ok=True)

    # Initialize the persistent ChromaDB client
    # PersistentClient saves all data to disk (vs. ephemeral in-memory client)
    # Suppress telemetry warnings from ChromaDB 0.4.22 compatibility issues
    with suppress_chromadb_warnings():
        client = chromadb.PersistentClient(path=db_path)

        # Get or create the collection
        # This is idempotent: safe to call multiple times
        collection = client.get_or_create_collection(name=collection_name)

    print(f"Vector database collection '{collection_name}' ready at {db_path}")
    return collection


def embed_and_store_chunks(chunks: List[Dict[str, str]], collection: Collection) -> None:
    """
    Generates embeddings for text chunks and stores them in ChromaDB.

    This function is the bridge between raw text and the vector database.
    It performs three critical steps:
    1. Convert text to vectors using Azure OpenAI embeddings
    2. Store vectors in ChromaDB
    3. Preserve metadata (source filename) for each vector

    Why metadata matters:
    When we retrieve relevant chunks later, we want to know which file they
    came from. This enables citation and helps users verify information.

    Embedding Process:
    - We send all chunk texts to Azure OpenAI in a single batch (efficient)
    - The API returns a vector (list of floats) for each text
    - Each vector is ~1536 dimensions for text-embedding-ada-002
    - Vectors capture semantic meaning: similar text = similar vectors

    Args:
        chunks: List of dicts with 'source' (filename) and 'content' (text)
        collection: ChromaDB collection to store embeddings in

    Returns:
        None (side effect: updates the collection)

    Raises:
        Exception: If embedding or storage fails (errors are logged)
    """
    if not chunks:
        print("No chunks to embed. Skipping.")
        return

    print(f"Embedding and storing {len(chunks)} chunks...")

    # Initialize Azure OpenAI client
    client = AzureOpenAI(
        api_key=settings.azure_openai_api_key,
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.openai_api_version,
    )

    # Prepare data for ChromaDB
    # ChromaDB requires three parallel lists: documents, metadatas, ids
    documents_to_add = []  # The actual text content
    metadatas_to_add = []  # Metadata dicts (source filename)
    ids_to_add = []  # Unique identifiers

    for chunk in chunks:
        documents_to_add.append(chunk["content"])
        metadatas_to_add.append({"source": chunk["source"]})

        # Generate a unique ID based on content hash
        # This ensures globally unique IDs across all batches and sources
        # Format: hash of (source + content)
        unique_string = f"{chunk['source']}_{chunk['content']}"
        chunk_hash = hashlib.sha256(unique_string.encode()).hexdigest()[:16]
        ids_to_add.append(f"chunk_{chunk_hash}")

    try:
        # Step 1: Generate embeddings for all chunks in one API call
        # This is more efficient than calling the API for each chunk individually
        print(f"Calling Azure OpenAI to generate {len(chunks)} embeddings...")

        response = client.embeddings.create(
            input=documents_to_add,  # List of texts to embed
            model=settings.embedding_model_name  # e.g., "text-embedding-ada-002"
        )

        # Extract the embedding vectors from the response
        # response.data is a list of Embedding objects, each with an .embedding attribute
        embeddings = [item.embedding for item in response.data]

        print(f"✓ Embeddings generated successfully ({len(embeddings)} vectors)")

        # Step 2: Store everything in ChromaDB
        # ChromaDB will:
        # - Store the vectors for similarity search
        # - Store the text content (for returning in results)
        # - Store the metadata (for citation/filtering)
        collection.add(
            embeddings=embeddings,  # List of vectors
            documents=documents_to_add,  # Corresponding texts
            metadatas=metadatas_to_add,  # Corresponding metadata
            ids=ids_to_add  # Unique identifiers
        )

        print(f"✓ Successfully embedded and stored {len(chunks)} chunks in vector database")

    except Exception as e:
        print(f"Error during embedding or storing: {e}")
        raise  # Re-raise the exception so the caller knows something went wrong
