"""
Tests for RAG retrieval node.

Tests all retrieval scenarios including:
- Successful context retrieval
- Empty knowledge base
- No relevant results
- Error handling
"""

import pytest
from unittest.mock import MagicMock, patch
from src.agent.nodes.retriever import retrieval_node
from src.agent.state import create_initial_state


class TestRetrievalNode:
    """Test retrieval node basic functionality."""

    @pytest.mark.asyncio
    async def test_retrieval_successful(self, mocker):
        """Test successful retrieval with relevant chunks."""
        state = create_initial_state("What are embeddings?", "rag_query")

        # Mock ChromaDB collection with documents
        mock_collection = MagicMock()
        mock_collection.count.return_value = 43  # Has documents

        # Mock vector store and chatbot retrieval
        mocker.patch(
            "src.agent.nodes.retriever.get_vector_database_collection",
            return_value=mock_collection
        )
        mocker.patch(
            "src.agent.nodes.retriever.retrieve_relevant_context",
            return_value=[
                "Embeddings are vector representations of text",
                "They capture semantic meaning in high-dimensional space",
                "Similar text has similar embeddings"
            ]
        )

        result = await retrieval_node(state)

        # Verify retrieved context
        assert result["retrieved_context"] is not None
        assert len(result["retrieved_context"]) == 3
        assert result["retrieved_context"][0]["content"] == "Embeddings are vector representations of text"
        assert result["retrieved_context"][0]["source"] == "knowledge_base"

        # Verify tool usage tracked
        assert len(result["tool_usage"]) > 0
        assert result["tool_usage"][0]["tool"] == "chromadb_retrieval"
        assert result["tool_usage"][0]["chunks_retrieved"] == 3

        # Verify reasoning steps
        assert any("Found 3 relevant chunks" in step for step in result["reasoning_steps"])

        # Verify next action
        assert result["next_action"] == "reason"

    @pytest.mark.asyncio
    async def test_retrieval_empty_knowledge_base(self, mocker):
        """Test handling of empty knowledge base."""
        state = create_initial_state("What are embeddings?", "rag_query")

        # Mock empty collection
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0  # Empty

        mocker.patch(
            "src.agent.nodes.retriever.get_vector_database_collection",
            return_value=mock_collection
        )

        result = await retrieval_node(state)

        # Verify empty context
        assert result["retrieved_context"] == []

        # Verify reasoning mentions empty knowledge base
        assert any("empty" in step.lower() for step in result["reasoning_steps"])

        # Should still proceed to reasoner
        assert result["next_action"] == "reason"

    @pytest.mark.asyncio
    async def test_retrieval_no_relevant_results(self, mocker):
        """Test when retrieval finds no relevant chunks."""
        state = create_initial_state("Unrelated query", "rag_query")

        # Mock collection with documents
        mock_collection = MagicMock()
        mock_collection.count.return_value = 43

        mocker.patch(
            "src.agent.nodes.retriever.get_vector_database_collection",
            return_value=mock_collection
        )
        # Return empty list (no relevant results)
        mocker.patch(
            "src.agent.nodes.retriever.retrieve_relevant_context",
            return_value=[]
        )

        result = await retrieval_node(state)

        # Verify empty context
        assert result["retrieved_context"] == []

        # Verify reasoning mentions no relevant context
        assert any("No relevant context" in step for step in result["reasoning_steps"])

        # Should still proceed to reasoner
        assert result["next_action"] == "reason"

    @pytest.mark.asyncio
    async def test_retrieval_error_handling(self, mocker):
        """Test error handling during retrieval."""
        state = create_initial_state("Test query", "rag_query")

        # Mock retrieval failure
        mocker.patch(
            "src.agent.nodes.retriever.get_vector_database_collection",
            side_effect=Exception("ChromaDB connection failed")
        )

        result = await retrieval_node(state)

        # Verify empty context on error
        assert result["retrieved_context"] == []

        # Verify reasoning mentions failure
        assert any("Failed to retrieve" in step for step in result["reasoning_steps"])

        # Should still proceed to reasoner (graceful degradation)
        assert result["next_action"] == "reason"


class TestRetrievalContextStorage:
    """Test how retrieval stores context in state."""

    @pytest.mark.asyncio
    async def test_context_format(self, mocker):
        """Test retrieved context format."""
        state = create_initial_state("Query", "rag_query")

        mock_collection = MagicMock()
        mock_collection.count.return_value = 10

        mocker.patch(
            "src.agent.nodes.retriever.get_vector_database_collection",
            return_value=mock_collection
        )
        mocker.patch(
            "src.agent.nodes.retriever.retrieve_relevant_context",
            return_value=["Chunk 1", "Chunk 2"]
        )

        result = await retrieval_node(state)

        # Verify format: list of dicts with 'content' and 'source'
        assert isinstance(result["retrieved_context"], list)
        assert all(isinstance(item, dict) for item in result["retrieved_context"])
        assert all("content" in item and "source" in item for item in result["retrieved_context"])
        assert result["retrieved_context"][0]["source"] == "knowledge_base"

    @pytest.mark.asyncio
    async def test_tool_usage_tracking(self, mocker):
        """Test that tool usage is properly tracked."""
        state = create_initial_state("Query", "rag_query")

        mock_collection = MagicMock()
        mock_collection.count.return_value = 10

        mocker.patch(
            "src.agent.nodes.retriever.get_vector_database_collection",
            return_value=mock_collection
        )
        mocker.patch(
            "src.agent.nodes.retriever.retrieve_relevant_context",
            return_value=["Short chunk", "Longer chunk with more text"]
        )

        result = await retrieval_node(state)

        # Verify tool usage details
        assert len(result["tool_usage"]) == 1
        tool_use = result["tool_usage"][0]
        assert tool_use["tool"] == "chromadb_retrieval"
        assert tool_use["chunks_retrieved"] == 2
        assert tool_use["total_chars"] > 0  # Sum of chunk lengths


class TestRetrievalIntegration:
    """Test retrieval integration with state management."""

    @pytest.mark.asyncio
    async def test_preserves_existing_state(self, mocker):
        """Test that retrieval doesn't lose existing state."""
        state = create_initial_state("Query", "rag_query")
        state["reasoning_steps"] = ["Previous step"]
        state["tool_usage"] = [{"tool": "previous_tool"}]

        mock_collection = MagicMock()
        mock_collection.count.return_value = 10

        mocker.patch(
            "src.agent.nodes.retriever.get_vector_database_collection",
            return_value=mock_collection
        )
        mocker.patch(
            "src.agent.nodes.retriever.retrieve_relevant_context",
            return_value=["Chunk"]
        )

        result = await retrieval_node(state)

        # Verify previous state preserved
        assert "Previous step" in result["reasoning_steps"]
        assert {"tool": "previous_tool"} in result["tool_usage"]

        # Verify new state added
        assert len(result["reasoning_steps"]) > len(state["reasoning_steps"])
        assert len(result["tool_usage"]) > len(state["tool_usage"])

    @pytest.mark.asyncio
    async def test_sets_correct_next_action(self, mocker):
        """Test that retrieval always routes to reasoner."""
        state = create_initial_state("Query", "rag_query")

        mock_collection = MagicMock()
        mock_collection.count.return_value = 10

        mocker.patch(
            "src.agent.nodes.retriever.get_vector_database_collection",
            return_value=mock_collection
        )
        mocker.patch(
            "src.agent.nodes.retriever.retrieve_relevant_context",
            return_value=["Chunk"]
        )

        result = await retrieval_node(state)

        # Should always go to reasoner after retrieval
        assert result["next_action"] == "reason"
