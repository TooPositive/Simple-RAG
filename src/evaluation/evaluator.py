"""
Agent evaluator for comprehensive performance measurement.

Provides the AgentEvaluator class that orchestrates all metrics
and produces an overall agent performance score.
"""

from typing import Dict
from src.agent.state import AgentState
from src.evaluation.metrics import (
    calculate_task_completion_score,
    calculate_reasoning_quality_score,
    calculate_tool_effectiveness_score,
    calculate_reflection_quality_score,
    calculate_output_quality_score,
    calculate_overall_score
)


class AgentEvaluator:
    """
    Comprehensive agent performance evaluator.
    
    Orchestrates all evaluation metrics to provide a complete
    assessment of agent performance.
    
    Example:
        >>> evaluator = AgentEvaluator()
        >>> scores = evaluator.evaluate(final_state)
        >>> print(f"Overall: {scores['overall_score']}")
    """
    
    def __init__(self):
        """Initialize the evaluator."""
        self.metrics = {
            "task_completion": calculate_task_completion_score,
            "reasoning_quality": calculate_reasoning_quality_score,
            "tool_effectiveness": calculate_tool_effectiveness_score,
            "reflection_quality": calculate_reflection_quality_score,
            "output_quality": calculate_output_quality_score
        }
    
    def evaluate(self, state: AgentState) -> Dict[str, float]:
        """
        Evaluate agent performance.
        
        Calculates all individual metrics and combines them into
        an overall performance score.
        
        Args:
            state: Final agent state to evaluate
        
        Returns:
            Dict[str, float]: Dictionary of all scores including overall_score
        
        Example:
            >>> evaluator = AgentEvaluator()
            >>> state = {"final_output": "Done", "is_complete": True}
            >>> scores = evaluator.evaluate(state)
            >>> scores["overall_score"]
            85.0
        """
        scores = {}
        
        # Calculate each metric
        for metric_name, metric_func in self.metrics.items():
            try:
                scores[metric_name] = metric_func(state)
            except Exception as e:
                # If a metric fails, assign 0
                scores[metric_name] = 0.0
        
        # Calculate overall score
        scores["overall_score"] = calculate_overall_score(scores)
        
        return scores
    
    def get_metric_names(self) -> list:
        """
        Get list of available metric names.
        
        Returns:
            list: List of metric names
        """
        return list(self.metrics.keys())
    
    def evaluate_metric(self, state: AgentState, metric_name: str) -> float:
        """
        Evaluate a single metric.
        
        Args:
            state: Agent state to evaluate
            metric_name: Name of the metric to calculate
        
        Returns:
            float: Score for the specified metric
        
        Raises:
            ValueError: If metric_name is not recognized
        """
        if metric_name not in self.metrics:
            raise ValueError(f"Unknown metric: {metric_name}")
        
        return self.metrics[metric_name](state)
