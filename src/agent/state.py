"""
Agent state management for LangGraph workflow.

This module defines the AgentState TypedDict that flows through
the LangGraph nodes, carrying all context, reasoning, and results.
"""

from typing import TypedDict, Annotated, Sequence, Optional, List, Dict
import operator
from langchain_core.messages import BaseMessage, HumanMessage


class AgentState(TypedDict):
    """
    State that flows through the agent graph.
    
    This TypedDict defines all the data that flows between nodes in the
    LangGraph workflow. Some fields use Annotated with operator.add to
    enable automatic list concatenation when merging states.
    """
    # Core task
    task: str  # The main task description
    task_type: str  # Type: "analyze_repo", "generate_post", "answer_question"
    
    # Messages history (automatically concatenated)
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # Repository analysis results
    repo_structure: Optional[Dict]  # Directory structure
    code_files: Optional[List[Dict]]  # Parsed source files
    dependencies: Optional[Dict]  # Project dependencies
    architecture: Optional[Dict]  # Architecture understanding
    code_symbols: Optional[Dict]  # 🔥 EXTRACTED CODE SYMBOLS (classes, functions, tests) - KEY FOR EVIDENCE-BASED ANALYSIS
    verification_outputs: Optional[Dict]  # 🔥 ACTUAL COMMAND OUTPUTS (pytest, coverage) - CEO REQUIREMENT FOR EVIDENCE-ONLY
    
    # Reasoning trail (automatically concatenated)
    reasoning_steps: Annotated[List[str], operator.add]
    reflection_notes: Annotated[List[str], operator.add]
    reflection_assessment: Optional[str]  # "good" or "needs_improvement"
    tool_usage: Annotated[List[Dict], operator.add]
    
    # RAG context (from v1.0)
    retrieved_context: Optional[List[Dict]]
    
    # Generation
    draft_content: Optional[str]
    final_output: Optional[str]
    output_before_reflection: Optional[str]  # For demo: output without reflection applied
    
    # Evaluation
    evaluation_scores: Optional[Dict[str, float]]
    evaluation_explanations: Optional[Dict[str, List[str]]]  # Evaluation explanations
    
    # Control flow
    next_action: str  # Next node to execute
    iteration_count: int  # Number of planning iterations
    generation_count: int  # Number of times output was generated
    max_iterations: int  # Maximum allowed iterations
    is_complete: bool  # Whether task is complete


def create_initial_state(
    task: str,
    task_type: str,
    max_iterations: int = 10
) -> AgentState:
    """
    Create an initial agent state.
    
    Args:
        task: The task description
        task_type: Type of task ("analyze_repo", "generate_post", etc.)
        max_iterations: Maximum iterations allowed (default: 10)
    
    Returns:
        AgentState: Initial state with default values
    
    Example:
        >>> state = create_initial_state(
        ...     task="Analyze this repository",
        ...     task_type="analyze_repo"
        ... )
        >>> state["iteration_count"]
        0
    """
    return AgentState(
        # Core task
        task=task,
        task_type=task_type,
        
        # Messages
        messages=[HumanMessage(content=task)],
        
        # Repository analysis (None initially)
        repo_structure=None,
        code_files=None,
        dependencies=None,
        architecture=None,
        code_symbols=None,
        verification_outputs=None,
        
        # Reasoning trail (empty lists)
        reasoning_steps=[],
        reflection_notes=[],
        reflection_assessment=None,
        tool_usage=[],
        
        # RAG context
        retrieved_context=None,
        
        # Generation
        draft_content=None,
        final_output=None,
        output_before_reflection=None,
        
        # Evaluation
        evaluation_scores=None,
        evaluation_explanations=None,
        
        # Control flow
        next_action="plan",
        iteration_count=0,
        generation_count=0,
        max_iterations=max_iterations,
        is_complete=False
    )


def update_state(
    state: AgentState,
    updates: Optional[Dict] = None,
    increment_iteration: bool = False
) -> AgentState:
    """
    Update agent state with new values.
    
    For list fields with Annotated[..., operator.add], new values are
    appended rather than replaced.
    
    Args:
        state: Current state
        updates: Dictionary of fields to update
        increment_iteration: Whether to increment iteration_count
    
    Returns:
        AgentState: Updated state
    
    Example:
        >>> state = create_initial_state("Test", "test")
        >>> updated = update_state(state, {
        ...     "next_action": "analyze",
        ...     "reasoning_steps": ["Step 1"]
        ... }, increment_iteration=True)
        >>> updated["iteration_count"]
        1
    """
    # Create a copy of the state
    new_state = AgentState(**state)
    
    # Apply updates
    if updates:
        for key, value in updates.items():
            if key in ["reasoning_steps", "reflection_notes", "tool_usage"]:
                # Append to lists instead of replacing
                if isinstance(value, list):
                    new_state[key] = state[key] + value
                else:
                    new_state[key] = state[key] + [value]
            elif key == "messages":
                # Append messages
                if isinstance(value, list):
                    new_state[key] = list(state[key]) + value
                else:
                    new_state[key] = list(state[key]) + [value]
            else:
                # Replace other fields
                new_state[key] = value
    
    # Increment iteration if requested
    if increment_iteration:
        new_state["iteration_count"] = state["iteration_count"] + 1
    
    return new_state


def is_state_complete(state: AgentState) -> bool:
    """
    Check if the agent state represents a completed task.
    
    A state is considered complete if:
    - is_complete flag is True, OR
    - max_iterations has been reached, OR
    - final_output has been generated
    
    Args:
        state: Agent state to check
    
    Returns:
        bool: True if state is complete
    
    Example:
        >>> state = create_initial_state("Test", "test")
        >>> is_state_complete(state)
        False
        >>> state["is_complete"] = True
        >>> is_state_complete(state)
        True
    """
    return (
        state["is_complete"] or
        state["iteration_count"] >= state["max_iterations"] or
        state["final_output"] is not None
    )
