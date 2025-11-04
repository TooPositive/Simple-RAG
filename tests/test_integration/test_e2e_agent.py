"""
End-to-end integration tests for the complete agent system.

Tests the full workflow from task input to evaluated output.
"""

import pytest
from src.agent.orchestrator import run_agent
from src.agent.state import create_initial_state


class TestEndToEndAgent:
    """Test complete agent workflow."""
    
    @pytest.mark.asyncio
    async def test_analyze_repo_workflow(self):
        """Test full workflow for repository analysis task."""
        task = "Analyze the repository structure"
        task_type = "analyze_repo"
        
        # Run the agent
        result = await run_agent(task, task_type)
        
        # Verify completion
        assert result is not None
        assert result["is_complete"] is True
        assert result["final_output"] is not None
        assert len(result["final_output"]) > 0
    
    @pytest.mark.asyncio
    async def test_agent_produces_evaluation_scores(self):
        """Test that agent produces evaluation scores."""
        task = "Test task"
        task_type = "test"
        
        result = await run_agent(task, task_type)
        
        # Verify evaluation scores exist
        assert "evaluation_scores" in result
        assert result["evaluation_scores"] is not None
        assert "overall_score" in result["evaluation_scores"]
    
    @pytest.mark.asyncio
    async def test_agent_accumulates_reasoning_steps(self):
        """Test that agent accumulates reasoning throughout workflow."""
        task = "Analyze repository"
        task_type = "analyze_repo"
        
        result = await run_agent(task, task_type)
        
        # Verify reasoning steps accumulated
        assert len(result["reasoning_steps"]) > 0
        # Should have steps from multiple nodes
        assert len(result["reasoning_steps"]) >= 3
    
    @pytest.mark.asyncio
    async def test_agent_uses_repository_tools(self):
        """Test that agent uses repository analysis tools."""
        task = "Analyze the codebase"
        task_type = "analyze_repo"
        
        result = await run_agent(task, task_type)
        
        # Verify repository analysis was performed
        assert result["repo_structure"] is not None
        assert result["dependencies"] is not None
        assert result["architecture"] is not None
    
    @pytest.mark.asyncio
    async def test_agent_performs_reflection(self):
        """Test that agent performs self-reflection."""
        task = "Test reflection"
        task_type = "test"
        
        result = await run_agent(task, task_type)
        
        # Verify reflection occurred
        assert len(result["reflection_notes"]) > 0
    
    @pytest.mark.asyncio
    async def test_agent_tracks_tool_usage(self):
        """Test that agent tracks tool usage."""
        task = "Analyze repository"
        task_type = "analyze_repo"
        
        result = await run_agent(task, task_type)
        
        # Verify tool usage tracked
        assert len(result["tool_usage"]) > 0
    
    @pytest.mark.asyncio
    async def test_agent_respects_iteration_limit(self):
        """Test that agent respects max iterations."""
        task = "Test task"
        task_type = "test"
        max_iterations = 5
        
        result = await run_agent(task, task_type, max_iterations=max_iterations)
        
        # Verify iteration limit respected
        assert result["iteration_count"] <= max_iterations


class TestAgentStateFlow:
    """Test state flow through the agent."""
    
    @pytest.mark.asyncio
    async def test_state_preserves_task_info(self):
        """Test that task information is preserved."""
        task = "Specific test task"
        task_type = "test"
        
        result = await run_agent(task, task_type)
        
        assert result["task"] == task
        assert result["task_type"] == task_type
    
    @pytest.mark.asyncio
    async def test_state_accumulates_messages(self):
        """Test that messages accumulate through workflow."""
        task = "Test"
        task_type = "test"
        
        result = await run_agent(task, task_type)
        
        # Should have initial message at minimum
        assert len(result["messages"]) >= 1
    
    @pytest.mark.asyncio
    async def test_state_marks_completion(self):
        """Test that state is marked complete."""
        task = "Test"
        task_type = "test"
        
        result = await run_agent(task, task_type)
        
        assert result["is_complete"] is True


class TestAgentEvaluation:
    """Test agent evaluation integration."""
    
    @pytest.mark.asyncio
    async def test_evaluation_scores_present(self):
        """Test that all evaluation scores are present."""
        task = "Test task"
        task_type = "test"
        
        result = await run_agent(task, task_type)
        
        scores = result["evaluation_scores"]
        assert "task_completion" in scores
        assert "reasoning_quality" in scores
        assert "tool_effectiveness" in scores
        assert "reflection_quality" in scores
        assert "output_quality" in scores
        assert "overall_score" in scores
    
    @pytest.mark.asyncio
    async def test_evaluation_scores_valid_range(self):
        """Test that evaluation scores are in valid range."""
        task = "Test"
        task_type = "test"
        
        result = await run_agent(task, task_type)
        
        scores = result["evaluation_scores"]
        for metric, score in scores.items():
            assert 0.0 <= score <= 100.0, f"{metric} score {score} out of range"
    
    @pytest.mark.asyncio
    async def test_high_quality_task_gets_high_score(self):
        """Test that completed task with good reasoning gets high score."""
        task = "Analyze repository"
        task_type = "analyze_repo"
        
        result = await run_agent(task, task_type)
        
        # Should have high task completion score
        assert result["evaluation_scores"]["task_completion"] >= 80.0
        # Should have reasonable overall score
        assert result["evaluation_scores"]["overall_score"] >= 50.0


class TestAgentRobustness:
    """Test agent robustness and error handling."""
    
    @pytest.mark.asyncio
    async def test_agent_handles_empty_task(self):
        """Test agent handles empty task gracefully."""
        task = ""
        task_type = "test"
        
        result = await run_agent(task, task_type)
        
        # Should still complete
        assert result is not None
        assert result["is_complete"] is True
    
    @pytest.mark.asyncio
    async def test_agent_handles_unknown_task_type(self):
        """Test agent handles unknown task type."""
        task = "Test"
        task_type = "unknown_type"
        
        result = await run_agent(task, task_type)
        
        # Should still complete
        assert result is not None
        assert result["is_complete"] is True
    
    @pytest.mark.asyncio
    async def test_agent_produces_output_for_any_task(self):
        """Test that agent always produces some output."""
        task = "Random task"
        task_type = "test"
        
        result = await run_agent(task, task_type)
        
        assert result["final_output"] is not None
        assert len(result["final_output"]) > 0


class TestAgentPerformance:
    """Test agent performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_agent_completes_in_reasonable_iterations(self):
        """Test that agent completes in reasonable number of iterations."""
        task = "Test"
        task_type = "test"
        
        result = await run_agent(task, task_type)
        
        # Should complete in less than max iterations
        assert result["iteration_count"] < result["max_iterations"]
    
    @pytest.mark.asyncio
    async def test_agent_workflow_is_deterministic(self):
        """Test that agent workflow is consistent."""
        task = "Test task"
        task_type = "test"
        
        # Run twice
        result1 = await run_agent(task, task_type)
        result2 = await run_agent(task, task_type)
        
        # Both should complete
        assert result1["is_complete"] is True
        assert result2["is_complete"] is True
        
        # Both should have similar structure
        assert len(result1["reasoning_steps"]) > 0
        assert len(result2["reasoning_steps"]) > 0
