"""
Tests for planning node with LLM integration.

Verifies task analysis, plan creation, and routing decisions.
"""

import pytest
from src.agent.nodes.planner import planning_node
from src.agent.state import create_initial_state


class TestPlanningNode:
    """Test planning node functionality."""
    
    @pytest.mark.asyncio
    async def test_planning_node_updates_state(self):
        """Test that planning node updates state."""
        state = create_initial_state("Analyze repository", "analyze_repo")
        
        result = await planning_node(state)
        
        assert result is not None
        assert "next_action" in result
        assert result["iteration_count"] == 1
    
    @pytest.mark.asyncio
    async def test_planning_node_sets_analyze_action(self):
        """Test planning for repository analysis."""
        state = create_initial_state("Analyze this repo", "analyze_repo")
        
        result = await planning_node(state)
        
        assert result["next_action"] == "analyze"
    
    @pytest.mark.asyncio
    async def test_planning_node_sets_retrieve_action(self):
        """Test planning for question answering."""
        state = create_initial_state("What is RAG?", "answer_question")
        
        result = await planning_node(state)
        
        assert result["next_action"] == "retrieve"
    
    @pytest.mark.asyncio
    async def test_planning_node_adds_reasoning_steps(self):
        """Test that planning adds reasoning steps."""
        state = create_initial_state("Test task", "test")
        
        result = await planning_node(state)
        
        assert len(result["reasoning_steps"]) > len(state["reasoning_steps"])
    
    @pytest.mark.asyncio
    async def test_planning_node_increments_iteration(self):
        """Test that iteration count is incremented."""
        state = create_initial_state("Test", "test")
        initial_count = state["iteration_count"]
        
        result = await planning_node(state)
        
        assert result["iteration_count"] == initial_count + 1
    
    @pytest.mark.asyncio
    async def test_planning_node_handles_empty_task(self):
        """Test planning with empty task."""
        state = create_initial_state("", "test")
        
        result = await planning_node(state)
        
        assert result is not None
        assert "next_action" in result


class TestPlanningLogic:
    """Test planning decision logic."""
    
    @pytest.mark.asyncio
    async def test_analyze_repo_task_type(self):
        """Test that analyze_repo type routes to analyze."""
        state = create_initial_state("Analyze code", "analyze_repo")
        
        result = await planning_node(state)
        
        assert result["next_action"] == "analyze"
    
    @pytest.mark.asyncio
    async def test_answer_question_task_type(self):
        """Test that answer_question type routes to retrieve."""
        state = create_initial_state("What is X?", "answer_question")
        
        result = await planning_node(state)
        
        assert result["next_action"] == "retrieve"
    
    @pytest.mark.asyncio
    async def test_default_task_type(self):
        """Test default routing for unknown task types."""
        state = create_initial_state("Do something", "unknown_type")
        
        result = await planning_node(state)
        
        assert result["next_action"] in ["analyze", "retrieve", "reason"]


class TestPlanningIntegration:
    """Integration tests for planning node."""
    
    @pytest.mark.asyncio
    async def test_planning_preserves_state_fields(self):
        """Test that planning preserves existing state fields."""
        state = create_initial_state("Test", "test")
        state["repo_structure"] = {"test": "data"}
        
        result = await planning_node(state)
        
        assert result["repo_structure"] == {"test": "data"}
        assert result["task"] == "Test"
    
    @pytest.mark.asyncio
    async def test_multiple_planning_iterations(self):
        """Test multiple planning iterations."""
        state = create_initial_state("Test", "test")
        
        # First iteration
        result1 = await planning_node(state)
        assert result1["iteration_count"] == 1
        
        # Second iteration
        result2 = await planning_node(result1)
        assert result2["iteration_count"] == 2
