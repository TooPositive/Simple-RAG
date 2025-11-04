"""
Tests for agent evaluator.

Verifies performance evaluation and scoring capabilities.
"""

import pytest
from src.agent.nodes.evaluator import evaluation_node
from src.agent.state import create_initial_state
from src.evaluation.evaluator import AgentEvaluator
from src.evaluation.metrics import (
    calculate_task_completion_score,
    calculate_reasoning_quality_score,
    calculate_overall_score
)


class TestEvaluationNode:
    """Test evaluation node functionality."""
    
    @pytest.mark.asyncio
    async def test_evaluation_node_adds_scores(self):
        """Test that evaluation adds scores to state."""
        state = create_initial_state("Test", "test")
        state["final_output"] = "Test output"
        
        result = await evaluation_node(state)
        
        assert result["evaluation_scores"] is not None
        assert isinstance(result["evaluation_scores"], dict)
    
    @pytest.mark.asyncio
    async def test_evaluation_node_has_required_scores(self):
        """Test that evaluation includes required score types."""
        state = create_initial_state("Test", "test")
        state["final_output"] = "Output"
        
        result = await evaluation_node(state)
        
        scores = result["evaluation_scores"]
        assert "task_completion" in scores
        assert "overall_score" in scores
    
    @pytest.mark.asyncio
    async def test_evaluation_preserves_state(self):
        """Test that evaluation preserves existing state."""
        state = create_initial_state("Test", "test")
        state["final_output"] = "Output"
        state["repo_structure"] = {"test": "data"}
        
        result = await evaluation_node(state)
        
        assert result["repo_structure"] == {"test": "data"}
        assert result["final_output"] == "Output"


class TestMetrics:
    """Test individual metric calculations."""
    
    def test_task_completion_score_with_output(self):
        """Test task completion score when output exists."""
        state = create_initial_state("Test", "test")
        state["final_output"] = "Complete output"
        state["is_complete"] = True
        
        score = calculate_task_completion_score(state)
        
        assert score >= 80.0
        assert score <= 100.0
    
    def test_task_completion_score_without_output(self):
        """Test task completion score when incomplete."""
        state = create_initial_state("Test", "test")
        
        score = calculate_task_completion_score(state)
        
        assert score >= 0.0
        assert score < 100.0
    
    def test_reasoning_quality_score(self):
        """Test reasoning quality scoring."""
        state = create_initial_state("Test", "test")
        state["reasoning_steps"] = ["Step 1", "Step 2", "Step 3"]
        
        score = calculate_reasoning_quality_score(state)
        
        assert score >= 0.0
        assert score <= 100.0
    
    def test_overall_score_calculation(self):
        """Test overall score calculation."""
        scores = {
            "task_completion": 90.0,
            "reasoning_quality": 80.0
        }
        
        overall = calculate_overall_score(scores)
        
        assert overall >= 0.0
        assert overall <= 100.0


class TestAgentEvaluatorClass:
    """Test AgentEvaluator class."""
    
    def test_evaluator_initialization(self):
        """Test that evaluator can be initialized."""
        evaluator = AgentEvaluator()
        
        assert evaluator is not None
    
    def test_evaluator_evaluate_method(self):
        """Test evaluator evaluate method."""
        evaluator = AgentEvaluator()
        state = create_initial_state("Test", "test")
        state["final_output"] = "Output"
        state["reasoning_steps"] = ["Step 1"]
        
        scores = evaluator.evaluate(state)
        
        assert isinstance(scores, dict)
        assert "overall_score" in scores
    
    def test_evaluator_returns_all_metrics(self):
        """Test that evaluator returns all metric types."""
        evaluator = AgentEvaluator()
        state = create_initial_state("Test", "test")
        state["final_output"] = "Complete"
        state["reasoning_steps"] = ["Step 1", "Step 2"]
        
        scores = evaluator.evaluate(state)
        
        assert "task_completion" in scores
        assert "reasoning_quality" in scores
        assert "overall_score" in scores
