"""
Tests for agent state management.

Verifies AgentState TypedDict definition and state management helpers.
"""

import pytest
from typing import get_type_hints
from src.agent.state import (
    AgentState,
    create_initial_state,
    update_state,
    is_state_complete
)


class TestAgentStateDefinition:
    """Test AgentState TypedDict structure."""
    
    def test_agent_state_has_required_fields(self):
        """Test that AgentState has all required fields."""
        hints = get_type_hints(AgentState)
        
        required_fields = [
            "task", "task_type", "messages", "repo_structure",
            "code_files", "dependencies", "architecture",
            "reasoning_steps", "reflection_notes", "tool_usage",
            "retrieved_context", "draft_content", "final_output",
            "evaluation_scores", "next_action", "iteration_count",
            "max_iterations", "is_complete"
        ]
        
        for field in required_fields:
            assert field in hints, f"Missing required field: {field}"
    
    def test_agent_state_field_types(self):
        """Test that AgentState fields have correct types."""
        hints = get_type_hints(AgentState)
        
        # Check string fields
        assert hints["task"].__name__ == "str"
        assert hints["task_type"].__name__ == "str"
        assert hints["next_action"].__name__ == "str"
        
        # Check int fields
        assert hints["iteration_count"].__name__ == "int"
        assert hints["max_iterations"].__name__ == "int"
        
        # Check bool fields
        assert hints["is_complete"].__name__ == "bool"


class TestStateCreation:
    """Test state creation helpers."""
    
    def test_create_initial_state_basic(self):
        """Test creating initial state with minimal parameters."""
        state = create_initial_state(
            task="Analyze this repository",
            task_type="analyze_repo"
        )
        
        assert state["task"] == "Analyze this repository"
        assert state["task_type"] == "analyze_repo"
        assert state["iteration_count"] == 0
        assert state["max_iterations"] == 10
        assert state["is_complete"] is False
        assert state["next_action"] == "plan"
        assert len(state["messages"]) == 1
        assert len(state["reasoning_steps"]) == 0
    
    def test_create_initial_state_custom_max_iterations(self):
        """Test creating state with custom max iterations."""
        state = create_initial_state(
            task="Test task",
            task_type="test",
            max_iterations=5
        )
        
        assert state["max_iterations"] == 5
    
    def test_create_initial_state_initializes_lists(self):
        """Test that lists are properly initialized."""
        state = create_initial_state(
            task="Test",
            task_type="test"
        )
        
        assert isinstance(state["messages"], list)
        assert isinstance(state["reasoning_steps"], list)
        assert isinstance(state["reflection_notes"], list)
        assert isinstance(state["tool_usage"], list)
    
    def test_create_initial_state_initializes_optionals_as_none(self):
        """Test that optional fields are None."""
        state = create_initial_state(
            task="Test",
            task_type="test"
        )
        
        assert state["repo_structure"] is None
        assert state["code_files"] is None
        assert state["dependencies"] is None
        assert state["architecture"] is None
        assert state["retrieved_context"] is None
        assert state["draft_content"] is None
        assert state["final_output"] is None
        assert state["evaluation_scores"] is None


class TestStateUpdate:
    """Test state update helpers."""
    
    def test_update_state_simple_fields(self):
        """Test updating simple state fields."""
        state = create_initial_state("Test", "test")
        
        updated = update_state(state, {
            "next_action": "analyze",
            "iteration_count": 1
        })
        
        assert updated["next_action"] == "analyze"
        assert updated["iteration_count"] == 1
        assert updated["task"] == "Test"  # Original fields preserved
    
    def test_update_state_appends_to_lists(self):
        """Test that list fields are appended, not replaced."""
        state = create_initial_state("Test", "test")
        state["reasoning_steps"] = ["Step 1"]
        
        updated = update_state(state, {
            "reasoning_steps": ["Step 2"]
        })
        
        assert "Step 1" in updated["reasoning_steps"]
        assert "Step 2" in updated["reasoning_steps"]
        assert len(updated["reasoning_steps"]) == 2
    
    def test_update_state_increments_iteration(self):
        """Test incrementing iteration count."""
        state = create_initial_state("Test", "test")
        
        updated = update_state(state, increment_iteration=True)
        
        assert updated["iteration_count"] == 1
    
    def test_update_state_marks_complete(self):
        """Test marking state as complete."""
        state = create_initial_state("Test", "test")
        
        updated = update_state(state, {
            "is_complete": True,
            "final_output": "Done"
        })
        
        assert updated["is_complete"] is True
        assert updated["final_output"] == "Done"


class TestStateValidation:
    """Test state validation helpers."""
    
    def test_is_state_complete_when_complete(self):
        """Test detecting completed state."""
        state = create_initial_state("Test", "test")
        state["is_complete"] = True
        
        assert is_state_complete(state) is True
    
    def test_is_state_complete_when_not_complete(self):
        """Test detecting incomplete state."""
        state = create_initial_state("Test", "test")
        
        assert is_state_complete(state) is False
    
    def test_is_state_complete_max_iterations_reached(self):
        """Test detecting completion by max iterations."""
        state = create_initial_state("Test", "test", max_iterations=3)
        state["iteration_count"] = 3
        
        assert is_state_complete(state) is True
    
    def test_is_state_complete_has_final_output(self):
        """Test detecting completion by final output."""
        state = create_initial_state("Test", "test")
        state["final_output"] = "Result"
        
        assert is_state_complete(state) is True


class TestStateIntegration:
    """Integration tests for state management."""
    
    def test_full_state_lifecycle(self):
        """Test complete state lifecycle."""
        # Create initial state
        state = create_initial_state(
            task="Analyze repository",
            task_type="analyze_repo"
        )
        
        # Simulate planning
        state = update_state(state, {
            "next_action": "analyze",
            "reasoning_steps": ["Analyzing repository structure"]
        }, increment_iteration=True)
        
        assert state["iteration_count"] == 1
        assert len(state["reasoning_steps"]) == 1
        
        # Simulate analysis
        state = update_state(state, {
            "repo_structure": {"files": 10},
            "reasoning_steps": ["Found 10 files"]
        }, increment_iteration=True)
        
        assert state["iteration_count"] == 2
        assert state["repo_structure"] is not None
        assert len(state["reasoning_steps"]) == 2
        
        # Simulate completion
        state = update_state(state, {
            "final_output": "Analysis complete",
            "is_complete": True
        })
        
        assert is_state_complete(state) is True
        assert state["final_output"] == "Analysis complete"
