# src/chatbot.py
"""
Chatbot Module for RAG System

This module implements the core RAG (Retrieval-Augmented Generation) logic:
1. Retrieve relevant context from the vector database
2. Format a prompt that combines the query with retrieved context
3. Generate an answer using an LLM
4. Orchestrate the entire pipeline through the RAGChatbot class

The RAG Pipeline:
User Question → Embed Question → Vector Search → Retrieve Context
→ Format Prompt → LLM Generation → Answer

This approach ensures the LLM answers are grounded in the actual knowledge base
rather than relying solely on its training data.
"""

from typing import List
from openai import AzureOpenAI
from chromadb.types import Collection
from src.config import settings
from src.data_loader import load_from_directory
from src.text_processor import chunk_text
from src.vector_store import (
    get_vector_database_collection,
    embed_and_store_chunks,
    suppress_chromadb_warnings
)


def retrieve_relevant_context(
    query: str,
    collection: Collection,
    n_results: int = 3
) -> List[str]:
    """
    Embeds a user query and retrieves the most semantically similar chunks from the vector database.

    This is the "R" (Retrieval) in RAG. It finds the most relevant information
    from our knowledge base to help answer the user's question.

    How it works:
    1. Convert the user's question to a vector using the same embedding model
       used for the documents
    2. Perform a similarity search in ChromaDB to find closest matching vectors
    3. Return the text content of the most similar chunks

    Why this works:
    - Similar meanings → similar vectors → high similarity scores
    - The embedding model creates a semantic space where related concepts cluster
    - Vector search is fast even with millions of documents

    Args:
        query: The user's natural language question
        collection: ChromaDB collection containing embedded documents
        n_results: Number of relevant chunks to retrieve (default: 3)

    Returns:
        List[str]: List of the most relevant text chunks

    Note:
        Returns empty list if retrieval fails or no results found
    """
    # Initialize Azure OpenAI client for embedding the query
    client = AzureOpenAI(
        api_key=settings.azure_openai_api_key,
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.openai_api_version,
    )

    try:
        # Step 1: Generate embedding for the user's query
        # CRITICAL: Must use the same embedding model as used for documents
        # Otherwise, the vectors won't be in the same semantic space
        response = client.embeddings.create(
            input=[query],  # Wrap in list as API expects a batch
            model=settings.embedding_model_name
        )

        # Extract the vector from the API response
        query_embedding = response.data[0].embedding

        # Step 2: Query the vector database for similar chunks
        # ChromaDB automatically computes similarity (typically cosine similarity)
        # and returns the n_results closest matches
        # Suppress telemetry warnings from ChromaDB 0.4.22
        with suppress_chromadb_warnings():
            results = collection.query(
                query_embeddings=[query_embedding],  # Wrap in list for batch API
                n_results=n_results,
                include=["documents"]  # Only need the text content, not metadata
            )

        # Step 3: Extract and return the document texts
        # Results structure: {"documents": [[doc1, doc2, doc3]], "ids": [[...]], ...}
        # The outer list is for batch queries, inner list is the results
        if results["documents"] and len(results["documents"]) > 0:
            return results["documents"][0]  # Return the first (and only) batch
        else:
            return []

    except Exception as e:
        print(f"Error during context retrieval: {e}")
        return []


def format_prompt(query: str, context: List[str]) -> str:
    """
    Formats the user query and retrieved context into a structured prompt for the LLM.

    Prompt engineering is crucial for RAG systems. A well-designed prompt:
    - Clearly instructs the LLM to use only the provided context
    - Reduces hallucination (making up answers)
    - Provides clear structure for the LLM to follow
    - Handles cases where the answer isn't in the context

    Args:
        query: The user's original question
        context: List of relevant text chunks retrieved from the database

    Returns:
        str: A formatted prompt ready for the LLM

    Example Output:
        ```
        You are a helpful AI assistant for the 'Databases for GenAI' lecture.
        Answer the following question based ONLY on the provided context.
        ...
        ---CONTEXT---
        Chunk 1 text here...
        ---
        Chunk 2 text here...
        ---END CONTEXT---

        QUESTION: What is RAG?
        ANSWER:
        ```
    """
    # Join context chunks with clear separators
    # This helps the LLM understand where one chunk ends and another begins
    context_str = "\n\n---\n\n".join(context)

    # Construct the prompt with clear instructions and structure
    prompt = f"""You are a helpful AI assistant for the 'Databases for GenAI' lecture.

Answer the following question based ONLY on the provided context.

If the answer is not in the context, reply with "I don't have enough information in the provided context to answer this question."

Do not use any prior knowledge or make assumptions beyond what is explicitly stated in the context.

---CONTEXT---
{context_str}
---END CONTEXT---

QUESTION: {query}

ANSWER:"""

    return prompt


def generate_llm_answer(prompt: str) -> str:
    """
    Sends the formatted prompt to the LLM and returns the generated answer.

    This is the "G" (Generation) in RAG. The LLM synthesizes information
    from the retrieved context to generate a coherent, natural language answer.

    Args:
        prompt: The fully formatted prompt with context and question

    Returns:
        str: The LLM's generated answer

    Note:
        Returns an error message if generation fails
    """
    # Initialize Azure OpenAI client
    client = AzureOpenAI(
        api_key=settings.azure_openai_api_key,
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.openai_api_version,
    )

    try:
        # Call the chat completions API
        # Using chat format (messages) rather than legacy completions
        response = client.chat.completions.create(
            model=settings.llm_model_name,  # e.g., "gpt-4o"
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on provided context."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,  # Balance between creativity and consistency
            max_tokens=1000,  # Limit response length
        )

        # Extract the text content from the response
        # Response structure: response.choices[0].message.content
        answer = response.choices[0].message.content

        return answer.strip() if answer else ""

    except Exception as e:
        print(f"Error during LLM answer generation: {e}")
        return "Sorry, I encountered an error while generating an answer."


class RAGChatbot:
    """
    High-level orchestrator for the entire RAG pipeline.

    This class provides a simple interface to a complex system:
    - Handles data ingestion on first run
    - Manages the vector database connection
    - Orchestrates retrieval and generation
    - Provides a single `ask()` method for users

    Usage:
        chatbot = RAGChatbot(data_dir="./data", db_dir="./chroma_db")
        answer = chatbot.ask("What is RAG?")
        print(answer)

    Design Pattern: Facade
    This class acts as a facade, hiding the complexity of the RAG pipeline
    behind a simple interface.
    """

    def __init__(self, data_dir: str = "./data", db_dir: str = "./chroma_db"):
        """
        Initializes the RAG chatbot.

        On initialization:
        1. Connects to the vector database
        2. If the database is empty, runs the full data ingestion pipeline:
           - Load documents from data_dir
           - Chunk the text
           - Generate embeddings
           - Store in vector database

        Args:
            data_dir: Directory containing knowledge base files (PDFs, audio, video)
            db_dir: Directory where ChromaDB will store its data

        Note:
            The ingestion only runs once. Subsequent initializations will use
            the existing database, making startup very fast.
        """
        print("\n" + "="*60)
        print("Initializing RAG Chatbot...")
        print("="*60)

        # Connect to vector database
        self.collection = get_vector_database_collection(db_path=db_dir)

        # Check if database is empty (first run)
        if self.collection.count() == 0:
            print("\n📦 Vector database is empty. Running data ingestion pipeline...\n")

            # Step 1: Load all documents from the data directory
            print("Step 1: Loading documents from directory...")
            documents = load_from_directory(data_dir)

            if not documents:
                print("⚠️  Warning: No documents found in data directory!")
                print("   Please add PDF, audio, or video files to proceed.")
                return

            print(f"✓ Loaded {len(documents)} documents")

            # Step 2: Chunk the documents
            print("\nStep 2: Chunking documents...")
            chunks = chunk_text(documents)
            print(f"✓ Created {len(chunks)} chunks")

            # Step 3: Generate embeddings and store
            print("\nStep 3: Generating embeddings and storing in vector database...")
            embed_and_store_chunks(chunks, self.collection)

            print("\n✅ Data ingestion complete!")
        else:
            # Database already has data, skip ingestion
            doc_count = self.collection.count()
            print(f"\n✓ Loaded existing database with {doc_count} documents")

        print("="*60)
        print("RAG Chatbot ready!")
        print("="*60 + "\n")

    def ask(self, query: str) -> str:
        """
        Ask the chatbot a question and get a RAG-powered answer.

        This method orchestrates the full RAG pipeline:
        1. Retrieve relevant context from vector database
        2. Format prompt with context and question
        3. Generate answer using LLM

        Args:
            query: The user's natural language question

        Returns:
            str: The generated answer

        Example:
            >>> chatbot = RAGChatbot()
            >>> answer = chatbot.ask("What are the production Do's for RAG?")
            >>> print(answer)
        """
        # Step 1: Retrieve relevant context
        context = retrieve_relevant_context(query, self.collection, n_results=3)

        if not context:
            return "I couldn't find any relevant information to answer your question."

        # Step 2: Format the prompt
        prompt = format_prompt(query, context)

        # Step 3: Generate the answer
        answer = generate_llm_answer(prompt)

        return answer
