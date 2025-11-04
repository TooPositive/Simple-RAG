"""
Tests for content generation node.

Verifies output generation and formatting capabilities.
"""

import pytest
from src.agent.nodes.generator import generation_node
from src.agent.state import create_initial_state


class TestGenerationNode:
    """Test generation node functionality."""
    
    @pytest.mark.asyncio
    async def test_generation_node_creates_output(self):
        """Test that generation creates final output."""
        state = create_initial_state("Test task", "test")
        state["reasoning_steps"] = ["Step 1", "Step 2"]
        
        result = await generation_node(state)
        
        assert result["final_output"] is not None
        assert len(result["final_output"]) > 0
    
    @pytest.mark.asyncio
    async def test_generation_node_marks_complete(self):
        """Test that generation marks task as complete."""
        state = create_initial_state("Test", "test")
        
        result = await generation_node(state)
        
        assert result["is_complete"] is True
    
    @pytest.mark.asyncio
    async def test_generation_includes_task(self):
        """Test that output includes relevant task content."""
        state = create_initial_state("Analyze repository", "analyze_repo")
        
        result = await generation_node(state)
        
        # Should contain repository analysis content
        assert "Repository" in result["final_output"] or "repository" in result["final_output"].lower()
    
    @pytest.mark.asyncio
    async def test_generation_includes_reasoning(self):
        """Test that output includes reasoning steps."""
        state = create_initial_state("Test", "test")
        state["reasoning_steps"] = ["Important step 1", "Important step 2"]
        
        result = await generation_node(state)
        
        output = result["final_output"]
        assert "Important step 1" in output or "step" in output.lower()
    
    @pytest.mark.asyncio
    async def test_generation_preserves_state(self):
        """Test that generation preserves existing state."""
        state = create_initial_state("Test", "test")
        state["repo_structure"] = {"test": "data"}
        
        result = await generation_node(state)
        
        assert result["repo_structure"] == {"test": "data"}
    
    @pytest.mark.asyncio
    async def test_generation_with_repo_analysis(self):
        """Test generation with repository analysis data."""
        state = create_initial_state("Analyze repo", "analyze_repo")
        state["repo_structure"] = {"files": 10}
        state["dependencies"] = {"count": 5}
        state["reasoning_steps"] = ["Analyzed structure"]
        
        result = await generation_node(state)
        
        assert result["final_output"] is not None
        assert result["is_complete"] is True


class TestGenerationQuality:
    """Test generation output quality."""
    
    @pytest.mark.asyncio
    async def test_generation_output_not_empty(self):
        """Test that output is not empty."""
        state = create_initial_state("Test", "test")
        
        result = await generation_node(state)
        
        assert len(result["final_output"].strip()) > 0
    
    @pytest.mark.asyncio
    async def test_generation_output_structure(self):
        """Test that output has proper structure."""
        state = create_initial_state("Test task", "test")
        state["reasoning_steps"] = ["Step 1"]
        
        result = await generation_node(state)
        
        output = result["final_output"]
        # Should have some structure (task, analysis, result)
        assert "Task:" in output or "task" in output.lower()
