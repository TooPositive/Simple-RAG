"""
Tests for reflection node with self-critique.

Verifies reflection and quality assessment capabilities.
"""

import pytest
from src.agent.nodes.reflector import reflection_node
from src.agent.state import create_initial_state


class TestReflectionNode:
    """Test reflection node functionality."""
    
    @pytest.mark.asyncio
    async def test_reflection_node_updates_state(self):
        """Test that reflection node updates state."""
        state = create_initial_state("Test task", "test")
        
        result = await reflection_node(state)
        
        assert result is not None
        assert "reflection_notes" in result
    
    @pytest.mark.asyncio
    async def test_reflection_node_adds_notes(self):
        """Test that reflection adds notes."""
        state = create_initial_state("Test", "test")
        initial_notes = len(state["reflection_notes"])
        
        result = await reflection_node(state)
        
        assert len(result["reflection_notes"]) > initial_notes
    
    @pytest.mark.asyncio
    async def test_reflection_node_sets_next_action(self):
        """Test that reflection sets next action."""
        state = create_initial_state("Test", "test")
        state["reasoning_steps"] = ["Step 1", "Step 2"]

        result = await reflection_node(state)

        assert result["next_action"] in ["end", "continue", "retry"]
    
    @pytest.mark.asyncio
    async def test_reflection_evaluates_reasoning(self):
        """Test that reflection evaluates reasoning quality."""
        state = create_initial_state("Test", "test")
        state["reasoning_steps"] = [
            "Analyzed repository structure",
            "Identified key components"
        ]
        
        result = await reflection_node(state)
        
        assert len(result["reflection_notes"]) > 0
    
    @pytest.mark.asyncio
    async def test_reflection_preserves_state(self):
        """Test that reflection preserves existing state."""
        state = create_initial_state("Test", "test")
        state["repo_structure"] = {"test": "data"}
        
        result = await reflection_node(state)
        
        assert result["repo_structure"] == {"test": "data"}


class TestReflectionDecisions:
    """Test reflection decision making."""
    
    @pytest.mark.asyncio
    async def test_reflection_decides_to_generate(self):
        """Test reflection deciding to end (proceed to evaluation)."""
        state = create_initial_state("Test", "test")
        state["reasoning_steps"] = ["Complete analysis"]

        result = await reflection_node(state)

        # Should decide to end (proceed to evaluation)
        assert result["next_action"] == "end"
    
    @pytest.mark.asyncio
    async def test_reflection_with_minimal_reasoning(self):
        """Test reflection with minimal reasoning."""
        state = create_initial_state("Test", "test")
        
        result = await reflection_node(state)
        
        assert result is not None
        assert "next_action" in result
