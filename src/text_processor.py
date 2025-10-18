# src/text_processor.py
"""
Text Processing Module for RAG Chatbot

This module handles text manipulation tasks, primarily chunking large documents
into smaller, semantically meaningful pieces for embedding and retrieval.

Key Concept: Why Chunking?
Embedding models have token limits, and retrieval is more effective with
focused, coherent chunks rather than entire documents. Good chunking preserves
semantic meaning while staying within size constraints.

Chunking Strategy:
We use LangChain's RecursiveCharacterTextSplitter, which:
1. Tries to split on paragraph boundaries (\n\n) first
2. Falls back to sentence boundaries (.) if needed
3. Finally splits on word boundaries ( ) as a last resort
4. Includes overlap between chunks to preserve context

This approach is superior to simple fixed-size splitting because it respects
the natural structure of the text.
"""

from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_text(
    documents: List[Dict[str, str]],
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[Dict[str, str]]:
    """
    Splits a list of documents into smaller, semantically meaningful chunks.

    This function takes documents loaded from various sources (PDFs, audio, video)
    and breaks their content into optimal-sized pieces for embedding and retrieval.

    Chunking Parameters Explained:
    - chunk_size (1000): Maximum characters per chunk. This balances between:
        * Too small: Loses context, more chunks to process
        * Too large: Exceeds embedding limits, less precise retrieval
    - chunk_overlap (200): Characters that overlap between consecutive chunks.
      This ensures that important context isn't lost at chunk boundaries.

    Process:
    1. Initialize the text splitter with specified parameters
    2. For each document:
        a. Split its content into multiple chunk strings
        b. Create new document dicts for each chunk
        c. Preserve source metadata (critical for citation/traceability)
    3. Return flattened list of all chunks from all documents

    Args:
        documents: List of dicts with 'source' (filename) and 'content' (text)
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks

    Returns:
        List[Dict]: List of chunk dicts, each with 'source' and 'content'

    Example:
        Input:
        [
            {'source': 'lecture.pdf', 'content': 'Very long text...' (2000 chars)}
        ]

        Output with chunk_size=1000, chunk_overlap=200:
        [
            {'source': 'lecture.pdf', 'content': 'First 1000 chars...'},
            {'source': 'lecture.pdf', 'content': 'Chars 800-1800...'}, # 200 overlap
            {'source': 'lecture.pdf', 'content': 'Chars 1600-2000...'}
        ]
    """
    # Initialize the recursive character text splitter
    # This splitter intelligently tries multiple separation strategies
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,  # Use character count for length
        # Default separators are ["\n\n", "\n", " ", ""] in that order
    )

    # Process each document and collect all chunks
    all_chunks = []

    for doc in documents:
        # Split the document's content into chunk strings
        # This returns a list of strings, not Document objects
        chunk_contents = text_splitter.split_text(doc["content"])

        # Create a new document dict for each chunk
        # CRITICAL: Preserve the 'source' metadata so we can trace
        # each chunk back to its original file
        for chunk_content in chunk_contents:
            chunk_doc = {
                "source": doc["source"],  # Preserve source filename
                "content": chunk_content  # This chunk's text
            }
            all_chunks.append(chunk_doc)

    print(f"Chunking complete: {len(documents)} documents → {len(all_chunks)} chunks")

    return all_chunks
