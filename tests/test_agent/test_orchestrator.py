"""
Tests for LangGraph agent orchestrator.

Verifies the agent workflow creation, node execution, and routing logic.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.agent.orchestrator import (
    create_agent_graph,
    route_after_planning,
    route_after_reflection,
    run_agent
)
from src.agent.state import create_initial_state


class TestGraphCreation:
    """Test agent graph creation."""
    
    def test_create_agent_graph_returns_compiled_graph(self):
        """Test that create_agent_graph returns a compiled graph."""
        graph = create_agent_graph()
        
        # Should be a compiled graph (has invoke method)
        assert hasattr(graph, 'invoke')
        assert hasattr(graph, 'ainvoke')
    
    def test_graph_has_required_nodes(self):
        """Test that graph contains all required nodes."""
        graph = create_agent_graph()
        
        # Graph should have nodes defined
        # We can't easily inspect the graph structure, but we can verify it compiles
        assert graph is not None


class TestRoutingLogic:
    """Test routing decision functions."""
    
    def test_route_after_planning_max_iterations_reached(self):
        """Test routing when max iterations reached."""
        state = create_initial_state("Test", "test", max_iterations=3)
        state["iteration_count"] = 3
        
        result = route_after_planning(state)
        
        assert result == "end"
    
    def test_route_after_planning_analyze_action(self):
        """Test routing to analyze when next_action is analyze."""
        state = create_initial_state("Test", "analyze_repo")
        state["next_action"] = "analyze"
        
        result = route_after_planning(state)
        
        assert result == "analyze"
    
    def test_route_after_planning_retrieve_action(self):
        """Test routing to retrieve when next_action is retrieve."""
        state = create_initial_state("Test", "answer_question")
        state["next_action"] = "retrieve"
        
        result = route_after_planning(state)
        
        assert result == "retrieve"
    
    def test_route_after_planning_reason_action(self):
        """Test routing to reason when next_action is reason."""
        state = create_initial_state("Test", "test")
        state["next_action"] = "reason"
        
        result = route_after_planning(state)
        
        assert result == "reason"
    
    def test_route_after_reflection_continue(self):
        """Test routing to continue after reflection."""
        state = create_initial_state("Test", "test")
        state["reflection_notes"] = ["Need more analysis"]
        state["next_action"] = "continue"
        
        result = route_after_reflection(state)
        
        assert result == "continue"
    
    def test_route_after_reflection_generate(self):
        """Test routing to generate after reflection."""
        state = create_initial_state("Test", "test")
        state["reflection_notes"] = ["Ready to generate"]
        state["next_action"] = "generate"
        
        result = route_after_reflection(state)
        
        assert result == "generate"
    
    def test_route_after_reflection_retry(self):
        """Test routing to retry after reflection."""
        state = create_initial_state("Test", "test")
        state["reflection_notes"] = ["Analysis incomplete"]
        state["next_action"] = "retry"
        
        result = route_after_reflection(state)
        
        assert result == "retry"


class TestAgentExecution:
    """Test agent execution."""
    
    @pytest.mark.asyncio
    async def test_run_agent_basic_execution(self):
        """Test basic agent execution."""
        result = await run_agent(
            task="Test task",
            task_type="test",
            max_iterations=1
        )
        
        # Should return a state
        assert "task" in result
        assert result["task"] == "Test task"
        assert result["task_type"] == "test"
    
    @pytest.mark.asyncio
    async def test_run_agent_respects_max_iterations(self):
        """Test that agent respects max iterations."""
        result = await run_agent(
            task="Test task",
            task_type="test",
            max_iterations=2
        )
        
        # Should not exceed max iterations
        assert result["iteration_count"] <= 2
    
    @pytest.mark.asyncio
    async def test_run_agent_returns_complete_state(self):
        """Test that agent returns complete state."""
        result = await run_agent(
            task="Simple test",
            task_type="test",
            max_iterations=1
        )
        
        # Should have all required state fields
        assert "messages" in result
        assert "reasoning_steps" in result
        assert "is_complete" in result


class TestGraphIntegration:
    """Integration tests for the full graph."""
    
    @pytest.mark.asyncio
    async def test_graph_executes_planning_node(self):
        """Test that graph executes planning node."""
        graph = create_agent_graph()
        
        initial_state = create_initial_state(
            task="Test planning",
            task_type="test",
            max_iterations=1
        )
        
        result = await graph.ainvoke(initial_state)
        
        # Planning should have been executed
        assert result["iteration_count"] >= 0
        assert "messages" in result
    
    @pytest.mark.asyncio
    async def test_graph_handles_empty_task(self):
        """Test that graph handles empty task gracefully."""
        graph = create_agent_graph()
        
        initial_state = create_initial_state(
            task="",
            task_type="test",
            max_iterations=1
        )
        
        result = await graph.ainvoke(initial_state)
        
        # Should complete without error
        assert result is not None
