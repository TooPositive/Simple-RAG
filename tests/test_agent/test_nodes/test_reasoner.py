"""
Tests for reasoning node with chain-of-thought.

Verifies multi-step reasoning and analysis capabilities.
"""

import pytest
from src.agent.nodes.reasoner import reasoning_node
from src.agent.state import create_initial_state


class TestReasoningNode:
    """Test reasoning node functionality."""
    
    @pytest.mark.asyncio
    async def test_reasoning_node_updates_state(self):
        """Test that reasoning node updates state."""
        state = create_initial_state("Test task", "test")
        
        result = await reasoning_node(state)
        
        assert result is not None
        assert "reasoning_steps" in result
    
    @pytest.mark.asyncio
    async def test_reasoning_node_adds_reasoning_steps(self):
        """Test that reasoning adds multiple steps."""
        state = create_initial_state("Analyze data", "test")
        initial_steps = len(state["reasoning_steps"])
        
        result = await reasoning_node(state)
        
        assert len(result["reasoning_steps"]) > initial_steps
    
    @pytest.mark.asyncio
    async def test_reasoning_node_sets_next_action(self):
        """Test that reasoning sets next action."""
        state = create_initial_state("Test", "test")
        
        result = await reasoning_node(state)
        
        assert result["next_action"] == "generate"
    
    @pytest.mark.asyncio
    async def test_reasoning_with_repo_analysis(self):
        """Test reasoning with repository analysis data."""
        state = create_initial_state("Analyze repo", "analyze_repo")
        state["repo_structure"] = {"files": 10}
        state["dependencies"] = {"count": 5}
        
        result = await reasoning_node(state)
        
        assert len(result["reasoning_steps"]) > 0
    
    @pytest.mark.asyncio
    async def test_reasoning_preserves_state(self):
        """Test that reasoning preserves existing state."""
        state = create_initial_state("Test", "test")
        state["code_files"] = [{"name": "test.py"}]
        
        result = await reasoning_node(state)
        
        assert result["code_files"] == [{"name": "test.py"}]


class TestReasoningLogic:
    """Test reasoning decision logic."""
    
    @pytest.mark.asyncio
    async def test_reasoning_analyzes_available_info(self):
        """Test that reasoning analyzes available information."""
        state = create_initial_state("Test", "test")
        state["repo_structure"] = {"analyzed": True}
        
        result = await reasoning_node(state)
        
        # Should have reasoning steps
        assert len(result["reasoning_steps"]) >= 2
    
    @pytest.mark.asyncio
    async def test_reasoning_handles_empty_state(self):
        """Test reasoning with minimal state."""
        state = create_initial_state("Test", "test")
        
        result = await reasoning_node(state)
        
        assert result is not None
        assert "reasoning_steps" in result
