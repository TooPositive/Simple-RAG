"""
Evaluation node for performance measurement.

This node evaluates the agent's overall performance using
the comprehensive evaluation framework.
"""

from src.agent.state import AgentState
from src.evaluation.evaluator import AgentEvaluator


async def evaluation_node(state: AgentState) -> AgentState:
    """
    Evaluate agent performance.
    
    Uses the AgentEvaluator to calculate comprehensive performance
    metrics including task completion, reasoning quality, tool
    effectiveness, reflection quality, and output quality.
    
    Args:
        state: Current agent state
    
    Returns:
        AgentState: Updated state with evaluation scores
    """
    new_state = dict(state)
    
    # Create evaluator and calculate all scores
    evaluator = AgentEvaluator()
    scores = evaluator.evaluate(state)
    
    new_state["evaluation_scores"] = scores
    
    return new_state
