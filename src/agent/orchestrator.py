"""
LangGraph agent orchestrator.

This module creates and manages the LangGraph workflow that
orchestrates all agent nodes and tools.
"""

import logging
from langgraph.graph import StateGraph, END
from src.agent.state import AgentState, create_initial_state
from src.agent.nodes.planner import planning_node
from src.agent.nodes.repo_analyzer import repo_analyzer_node
from src.agent.nodes.retriever import retrieval_node
from src.agent.nodes.reasoner import reasoning_node
from src.agent.nodes.reflector import reflection_node
from src.agent.nodes.generator import generation_node
from src.agent.nodes.evaluator import evaluation_node

# Set up logging
logger = logging.getLogger(__name__)


def create_agent_graph() -> StateGraph:
    """
    Create the LangGraph agent workflow.
    
    This function constructs the complete agent graph with all nodes
    and conditional routing logic.
    
    Returns:
        StateGraph: Compiled LangGraph workflow
    
    Example:
        >>> graph = create_agent_graph()
        >>> result = await graph.ainvoke(initial_state)
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("planner", planning_node)
    workflow.add_node("repo_analyzer", repo_analyzer_node)
    workflow.add_node("retriever", retrieval_node)
    workflow.add_node("reasoner", reasoning_node)
    workflow.add_node("reflector", reflection_node)
    workflow.add_node("generator", generation_node)
    workflow.add_node("evaluator", evaluation_node)
    
    # Define edges
    workflow.set_entry_point("planner")
    
    # Conditional routing after planning
    workflow.add_conditional_edges(
        "planner",
        route_after_planning,
        {
            "analyze": "repo_analyzer",
            "retrieve": "retriever",  # RAG retrieval from ChromaDB
            "reason": "reasoner",
            "end": "evaluator"  # ALWAYS evaluate before ending
        }
    )
    
    # Repository analyzer flows to reasoner
    workflow.add_edge("repo_analyzer", "reasoner")
    
    # Retriever flows to reasoner (to process retrieved context)
    workflow.add_edge("retriever", "reasoner")
    
    # Reasoner flows to generator (creates output)
    workflow.add_edge("reasoner", "generator")
    
    # Generator flows to reflector (critiques actual output)
    workflow.add_edge("generator", "reflector")
    
    # Reflector can either finish or request more analysis
    workflow.add_conditional_edges(
        "reflector",
        route_after_reflection,
        {
            "continue": "planner",  # Loop back to get more data/tools
            "retry": "generator",    # Regenerate with reflection notes
            "end": "evaluator"       # Good enough, evaluate
        }
    )
    
    # Evaluator is the end
    workflow.add_edge("evaluator", END)
    
    return workflow.compile()


def route_after_planning(state: AgentState) -> str:
    """
    Decide next action after planning node.
    
    Routes based on:
    - Max iterations reached -> end
    - next_action field in state
    
    Args:
        state: Current agent state
    
    Returns:
        str: Next node name ("analyze", "retrieve", "reason", or "end")
    """
    # Check if max iterations reached
    if state["iteration_count"] > state["max_iterations"]:
        return "end"
    
    # Route based on next_action
    next_action = state.get("next_action", "reason")
    
    if next_action in ["analyze", "retrieve", "reason"]:
        return next_action
    
    return "end"


def route_after_reflection(state: AgentState) -> str:
    """
    Decide next action after reflection node.
    
    Routes based on the reflection's decision:
    - "continue" → go back to planner for more data/tools
    - "retry" → regenerate output with improvements
    - "end" → proceed to evaluation
    
    Args:
        state: Current agent state
    
    Returns:
        str: Next node name ("continue", "retry", or "end")
    """
    next_action = state.get("next_action", "end")
    
    # Validate next_action is one of the expected values
    if next_action in ["continue", "retry", "end"]:
        return next_action
    
    # Default to end if unclear (prevent errors)
    print(f"  ⚠️  Invalid next_action '{next_action}', defaulting to 'end'")
    return "end"


async def run_agent(
    task: str,
    task_type: str = "analyze_repo",
    max_iterations: int = 1,  # Single pass through workflow (no looping needed)
    previous_repo_data: dict = None
) -> AgentState:
    """
    Run the agent on a task.
    
    This is the main entry point for executing the agent workflow.
    
    Args:
        task: Task description
        task_type: Type of task ("analyze_repo", "generate_post", etc.)
        max_iterations: Maximum iterations allowed
        previous_repo_data: Optional cached repository data from previous query
    
    Returns:
        AgentState: Final state after execution
    
    Example:
        >>> result = await run_agent(
        ...     task="Analyze this repository",
        ...     task_type="analyze_repo"
        ... )
        >>> print(result["final_output"])
    """
    # Create initial state
    initial_state = create_initial_state(
        task=task,
        task_type=task_type,
        max_iterations=max_iterations
    )
    
    # Inject previous repository data if available (for follow-up questions)
    if previous_repo_data:
        print("  📦 Using cached repository data from previous query")
        initial_state["repo_structure"] = previous_repo_data.get('repo_structure', {})
        initial_state["dependencies"] = previous_repo_data.get('dependencies', {})
        initial_state["architecture"] = previous_repo_data.get('architecture', {})
        initial_state["code_files"] = previous_repo_data.get('code_files', [])
        initial_state["code_symbols"] = previous_repo_data.get('code_symbols', {})
        initial_state["verification_outputs"] = previous_repo_data.get('verification_outputs', {})

    # Create and run graph with proper exception handling
    graph = create_agent_graph()

    try:
        final_state = await graph.ainvoke(initial_state)
    except Exception as e:
        logger.error(f"Agent execution failed: {e}", exc_info=True)
        print(f"  ❌ Agent execution encountered an error: {type(e).__name__}")
        print(f"  💡 Creating fallback response...")

        # Create fallback state with error information
        final_state = initial_state.copy()
        final_state["final_output"] = (
            f"I apologize, but I encountered an error while processing your request.\n\n"
            f"**Error Type:** {type(e).__name__}\n"
            f"**Details:** {str(e)[:200]}\n\n"
            f"This may be due to:\n"
            f"- Missing or invalid API credentials\n"
            f"- Network connectivity issues\n"
            f"- Rate limiting from API providers\n"
            f"- Invalid input format\n\n"
            f"Please check your configuration and try again."
        )
        final_state["is_complete"] = False
        final_state["evaluation_scores"] = {
            "task_completion": 0.0,
            "reasoning_quality": 0.0,
            "tool_effectiveness": 0.0,
            "reflection_quality": 0.0,
            "output_quality": 0.0,
            "overall_score": 0.0
        }

    # Generate evaluation explanations if scores exist
    if final_state.get("evaluation_scores"):
        try:
            from src.evaluation.explanations import generate_all_explanations
            final_state["evaluation_explanations"] = generate_all_explanations(
                final_state,
                final_state["evaluation_scores"]
            )
        except Exception as e:
            logger.warning(f"Failed to generate evaluation explanations: {e}")
            # Continue without explanations rather than failing

    return final_state
