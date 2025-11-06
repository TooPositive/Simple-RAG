"""
Planning node for task analysis and routing.

This node analyzes the incoming task and creates an execution plan.
"""

from src.agent.state import AgentState


async def planning_node(state: AgentState) -> AgentState:
    """
    Analyze task and create execution plan.
    
    Determines what actions are needed based on the task type
    and current state.
    
    Args:
        state: Current agent state
    
    Returns:
        AgentState: Updated state with next_action set
    """
    # Planning logic based on task type
    task_type = state["task_type"]
    task = state["task"]
    
    # Check if we already have repo data (from cache or previous analysis)
    has_repo_data = bool(state.get("repo_structure") or state.get("code_files"))
    
    # Initialize skip flags
    skip_reasoning = False
    skip_reflection = False

    if task_type == "analyze_repo":
        # Always analyze for explicit repo analysis requests
        next_action = "analyze"
        plan_note = f"Task requires repository analysis"
        skip_reasoning = False
        skip_reflection = False  # Repo analysis benefits from reflection
    elif task_type == "answer_question":
        # RAG retrieval for knowledge base questions
        next_action = "retrieve"
        plan_note = f"Task requires knowledge base retrieval"
        skip_reasoning = False
        skip_reflection = True  # RAG questions don't need reflection
    elif task_type == "generate_content":
        # Content generation (LinkedIn posts, etc.)
        skip_reasoning = False
        skip_reflection = True  # Content generation doesn't benefit from reflection loops
        if has_repo_data:
            next_action = "reason"
            plan_note = f"Task requires content generation using cached repo data"
        else:
            # If no repo data but generating content about repo, analyze first
            next_action = "analyze"
            plan_note = f"Task requires repo analysis before content generation"
    else:
        # General tasks - check if repo data would be useful
        task_lower = task.lower()
        code_keywords = ['where', 'which', 'file', 'class', 'function', 'import', 'use', 'used']

        # Detect trivial queries (math, simple greetings, etc.)
        trivial_patterns = [
            # Math operations
            any(op in task_lower for op in ['+', '-', '*', '/', '=', 'plus', 'minus', 'times', 'divided']),
            # Very short queries
            len(task.strip().split()) <= 3 and not any(kw in task_lower for kw in code_keywords),
            # Common trivial queries
            any(word in task_lower for word in ['hello', 'hi', 'hey', 'thanks', 'thank you'])
        ]

        is_trivial = any(trivial_patterns)

        if any(keyword in task_lower for keyword in code_keywords) and not has_repo_data:
            # Looks like a code question but no data - analyze first
            next_action = "analyze"
            plan_note = f"Code-specific question detected - analyzing repository"
            skip_reasoning = False
            skip_reflection = True  # Code questions don't benefit from reflection loops
        elif is_trivial:
            # Trivial query - skip reasoning and reflection entirely
            next_action = "reason"  # Will be handled as passthrough
            plan_note = f"Simple query detected - direct response"
            skip_reasoning = True
            skip_reflection = True
        else:
            # General reasoning task
            next_action = "reason"
            plan_note = f"Task requires direct reasoning"
            skip_reasoning = False
            skip_reflection = True  # Most general tasks don't need reflection

    # Update state
    new_state = dict(state)
    current_iteration = state["iteration_count"] + 1
    new_state["next_action"] = next_action
    new_state["skip_reasoning"] = skip_reasoning
    new_state["skip_reflection"] = skip_reflection
    new_state["reasoning_steps"] = state["reasoning_steps"] + [
        f"Planning: {plan_note} → next action: {next_action}"
    ]
    new_state["iteration_count"] = current_iteration

    return new_state
