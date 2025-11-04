"""
Evaluation framework for agent performance measurement.

Provides comprehensive metrics and scoring for:
    - Task completion
    - Reasoning quality
    - Tool effectiveness
    - Self-reflection quality
    - Output quality

Example:
    >>> from src.evaluation.evaluator import AgentEvaluator
    >>> evaluator = AgentEvaluator()
    >>> scores = evaluator.evaluate(agent_state, task)
"""

__all__ = ["metrics", "evaluator"]
