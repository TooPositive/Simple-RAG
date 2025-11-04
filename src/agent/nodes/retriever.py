"""
RAG Retrieval node for knowledge base questions.

This node queries ChromaDB to retrieve relevant context from the
ingested PDFs, MP4 transcripts, and other documents.
"""

from src.agent.state import AgentState
from src.vector_store import get_vector_database_collection
from src.chatbot import retrieve_relevant_context
from typing import List


async def retrieval_node(state: AgentState) -> AgentState:
    """
    Retrieve relevant context from ChromaDB vector store.
    
    This is the classic RAG (Retrieval-Augmented Generation) functionality
    from v1.0. It searches the knowledge base for relevant information
    to answer questions about AI, embeddings, etc.
    
    Args:
        state: Current agent state
    
    Returns:
        AgentState: Updated state with retrieved_context populated
    """
    new_state = dict(state)
    
    task = state["task"]
    
    try:
        print("📚 Retrieving from knowledge base (ChromaDB)...")
        
        # Get the ChromaDB collection
        collection = get_vector_database_collection(
            db_path="./chroma_db",
            collection_name="documents"
        )
        
        # Check if collection has any documents
        count = collection.count()
        if count == 0:
            print("  ⚠️  Knowledge base is empty!")
            print("  💡 Run 'python ingest_data.py' to load data first")
            new_state["retrieved_context"] = []
            new_state["reasoning_steps"] = state["reasoning_steps"] + [
                "Retrieval: Knowledge base is empty - no context retrieved"
            ]
            new_state["next_action"] = "reason"
            return new_state
        
        print(f"  ✓ Knowledge base has {count} documents")
        
        # Retrieve relevant chunks (top 3 by default)
        relevant_chunks = retrieve_relevant_context(
            query=task,
            collection=collection,
            n_results=3
        )
        
        if relevant_chunks:
            print(f"  ✓ Retrieved {len(relevant_chunks)} relevant chunks")
            
            # Store in state as list of dicts with metadata
            new_state["retrieved_context"] = [
                {"content": chunk, "source": "knowledge_base"}
                for chunk in relevant_chunks
            ]
            
            # Add tool usage tracking
            new_state["tool_usage"] = state["tool_usage"] + [{
                "tool": "chromadb_retrieval",
                "chunks_retrieved": len(relevant_chunks),
                "total_chars": sum(len(c) for c in relevant_chunks)
            }]
            
            new_state["reasoning_steps"] = state["reasoning_steps"] + [
                f"Retrieval: Found {len(relevant_chunks)} relevant chunks from knowledge base"
            ]
        else:
            print("  ⚠️  No relevant context found")
            new_state["retrieved_context"] = []
            new_state["reasoning_steps"] = state["reasoning_steps"] + [
                "Retrieval: No relevant context found in knowledge base"
            ]
        
        # Next: Go to reasoner to process the retrieved context
        new_state["next_action"] = "reason"
        
    except Exception as e:
        print(f"  ❌ Retrieval failed: {e}")
        print(f"  💡 Make sure ChromaDB is set up and data is ingested")
        new_state["retrieved_context"] = []
        new_state["reasoning_steps"] = state["reasoning_steps"] + [
            f"Retrieval: Failed to retrieve context - {str(e)}"
        ]
        new_state["next_action"] = "reason"
    
    return new_state
