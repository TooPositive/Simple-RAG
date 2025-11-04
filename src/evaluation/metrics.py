"""
Evaluation metrics for agent performance.

Provides individual metric calculations:
    - Task completion score
    - Reasoning quality score
    - Tool effectiveness score
    - Reflection quality score
    - Output quality score
    
Production-quality implementation with:
    - Task-type aware evaluation
    - Self-reflection incorporation verification
    - Tool result usage validation
    - Quality indicators over generic keywords
"""

from typing import Dict, Tuple
from src.agent.state import AgentState


def calculate_task_completion_score(state: AgentState) -> float:
    """
    Calculate task completion score (0-100).
    
    Evaluates whether the task was successfully completed based on:
    - Presence of final output
    - is_complete flag
    - Iteration count vs max iterations
    
    Args:
        state: Agent state to evaluate
    
    Returns:
        float: Score from 0-100
    
    Example:
        >>> state = {"final_output": "Done", "is_complete": True}
        >>> calculate_task_completion_score(state)
        100.0
    """
    score = 0.0
    
    # Has final output (50 points)
    if state.get("final_output"):
        score += 50.0
    
    # Marked as complete (30 points)
    if state.get("is_complete"):
        score += 30.0
    
    # Completed within iteration limit (20 points)
    if state.get("iteration_count", 0) < state.get("max_iterations", 10):
        score += 20.0
    elif state.get("iteration_count", 0) == state.get("max_iterations", 10):
        score += 10.0  # Partial credit
    
    return min(score, 100.0)


def calculate_reasoning_quality_score(state: AgentState) -> float:
    """
    Calculate reasoning quality score (0-100).
    
    Evaluates the quality of reasoning based on:
    - Number of reasoning steps
    - Depth of analysis
    - Use of available information
    
    Args:
        state: Agent state to evaluate
    
    Returns:
        float: Score from 0-100
    
    Example:
        >>> state = {"reasoning_steps": ["Step 1", "Step 2", "Step 3"]}
        >>> calculate_reasoning_quality_score(state)
        75.0
    """
    score = 0.0
    
    reasoning_steps = state.get("reasoning_steps", [])
    num_steps = len(reasoning_steps)
    
    # Base score for having reasoning steps (40 points)
    if num_steps > 0:
        score += 40.0
    
    # Quality based on number of steps (40 points)
    if num_steps >= 5:
        score += 40.0
    elif num_steps >= 3:
        score += 30.0
    elif num_steps >= 1:
        score += 20.0
    
    # Bonus for reflection (20 points)
    reflection_notes = state.get("reflection_notes", [])
    if len(reflection_notes) > 0:
        score += 20.0
    
    return min(score, 100.0)


def calculate_tool_effectiveness_score(state: AgentState) -> float:
    """
    Calculate tool effectiveness score (0-100).
    
    Evaluates how effectively tools were used based on:
    - Number of tools used
    - Appropriateness of tool selection
    - Results obtained from tools
    
    Args:
        state: Agent state to evaluate
    
    Returns:
        float: Score from 0-100
    
    Example:
        >>> state = {"tool_usage": [{"tool": "repo_analysis"}]}
        >>> calculate_tool_effectiveness_score(state)
        80.0
    """
    score = 0.0
    
    tool_usage = state.get("tool_usage", [])
    num_tools = len(tool_usage)
    
    # Base score for using tools (50 points)
    if num_tools > 0:
        score += 50.0
    
    # Additional points for multiple tools (30 points)
    if num_tools >= 3:
        score += 30.0
    elif num_tools >= 2:
        score += 20.0
    elif num_tools >= 1:
        score += 10.0
    
    # Bonus for having results (20 points)
    has_repo_data = state.get("repo_structure") is not None
    has_dependencies = state.get("dependencies") is not None
    
    if has_repo_data and has_dependencies:
        score += 20.0
    elif has_repo_data or has_dependencies:
        score += 10.0
    
    return min(score, 100.0)


def calculate_reflection_quality_score(state: AgentState) -> float:
    """
    Calculate reflection quality score (0-100).
    
    Evaluates the quality of self-reflection based on:
    - Presence of reflection notes
    - Depth and quality of self-critique
    - Incorporation in final output (CRITICAL - proves reflection was used)
    
    Args:
        state: Agent state to evaluate
    
    Returns:
        float: Score from 0-100
    
    Example:
        >>> state = {"reflection_notes": ["Lacks specificity"], 
        ...          "final_output": "### How Self-Reflection Improved: Added details (addressing specificity)"}
        >>> calculate_reflection_quality_score(state)
        100.0
    """
    score = 0.0
    
    reflection_notes = state.get("reflection_notes", [])
    num_notes = len(reflection_notes)
    
    # Base score for having reflections (30 points)
    if num_notes > 0:
        score += 30.0
    
    # Quality based on depth of reflections (30 points)
    if num_notes >= 3:
        score += 30.0
    elif num_notes >= 2:
        score += 20.0
    elif num_notes >= 1:
        score += 15.0
    
    # CRITICAL: Check if reflection was incorporated in output (40 points)
    # This is the proof that self-reflection actually influenced the output
    has_reflection_section, incorporation_score = _check_reflection_incorporated(state)
    
    if has_reflection_section:
        # Strong evidence of incorporation
        score += 40.0
    elif num_notes > 0:
        # Has reflection but no explicit incorporation section
        # Check if output at least mentions addressing concerns
        output_lower = state.get("final_output", "").lower()
        implicit_addressing = any(term in output_lower for term in 
                                 ['addressing', 'improved', 'enhanced', 'added', 'included'])
        if implicit_addressing:
            score += 20.0  # Partial credit for implicit addressing
    
    return min(score, 100.0)


def _detect_output_type(state: AgentState) -> str:
    """
    Detect the type of output for task-aware evaluation.
    
    Returns:
        str: Output type - 'code_question', 'linkedin_post', 'repository_analysis', 'general'
    """
    task = state.get("task", "").lower()
    task_type = state.get("task_type", "")
    
    # LinkedIn post detection
    if "linkedin" in task or "post" in task:
        return "linkedin_post"
    
    # Code-specific question detection
    code_keywords = ['where', 'which file', 'which class', 'which function', 
                     'show me', 'find', 'locate', 'how is', 'used in']
    if any(kw in task for kw in code_keywords):
        return "code_question"
    
    # Repository analysis detection
    if task_type == "analyze_repo" and not any(kw in task for kw in code_keywords):
        return "repository_analysis"
    
    return "general"


def _check_reflection_incorporated(state: AgentState) -> Tuple[bool, float]:
    """
    Check if self-reflection was incorporated in the output.
    
    Returns:
        Tuple[bool, float]: (has_section, quality_score)
    """
    output = state.get("final_output", "").lower()
    reflection_notes = state.get("reflection_notes", [])
    
    # Check for explicit reflection section
    has_section = "how self-reflection improved" in output or "self-reflection impact" in output
    
    if not has_section:
        return False, 0.0
    
    # Check if it references critique points
    score = 15.0  # Base score for having section
    
    # Look for critique-related terms in output
    critique_terms = ['addressing', 'critique', 'mentioned', 'noted', 'responding to', 
                      'improving', 'enhancement', 'added', 'included']
    
    references_found = sum(1 for term in critique_terms if term in output)
    if references_found >= 3:
        score += 15.0  # Strong references
    elif references_found >= 1:
        score += 10.0  # Some references
    
    return True, min(score, 30.0)


def _evaluate_code_question_quality(state: AgentState) -> float:
    """
    Evaluate output quality for code-specific questions.
    
    Looks for:
    - File paths and names
    - Line numbers
    - Code excerpts/imports
    - Function/class names
    - Self-reflection incorporation
    """
    output = state.get("final_output", "")
    output_lower = output.lower()
    score = 0.0
    
    # Specificity (40 points)
    # File references (10 pts)
    has_file_path = ".py" in output or "/" in output or "file:" in output_lower
    if has_file_path:
        score += 10.0
    
    # Line numbers (10 pts)
    has_line_numbers = "line" in output_lower and any(c.isdigit() for c in output)
    if has_line_numbers:
        score += 10.0
    
    # Code excerpts (10 pts)
    has_code = ("import" in output_lower or "from" in output_lower or 
                "def" in output_lower or "class" in output_lower or "`" in output)
    if has_code:
        score += 10.0
    
    # Function/class names (10 pts)
    has_identifiers = any(c.isupper() for c in output) or "()" in output
    if has_identifiers:
        score += 10.0
    
    # Completeness (30 points)
    output_length = len(output)
    if output_length >= 500:
        score += 15.0  # Comprehensive
    elif output_length >= 200:
        score += 12.0  # Adequate
    elif output_length >= 100:
        score += 8.0   # Minimal
    
    # Has context/explanation (15 pts)
    has_context = output_length >= 200 and ("used in" in output_lower or 
                                            "function" in output_lower or
                                            "purpose" in output_lower)
    if has_context:
        score += 15.0
    
    # Self-reflection integration (30 points)
    has_reflection_section, reflection_score = _check_reflection_incorporated(state)
    score += reflection_score
    
    return min(score, 100.0)


def _evaluate_linkedin_post_quality(state: AgentState) -> float:
    """
    Evaluate output quality for LinkedIn posts.
    
    Looks for:
    - Professional structure
    - Hashtags
    - Engaging elements (emojis, formatting)
    - Technical specifics
    - Self-reflection demonstration
    """
    output = state.get("final_output", "")
    output_lower = output.lower()
    score = 0.0
    
    # Professional structure (30 points)
    has_opening = any(word in output_lower[:200] for word in ['excited', 'thrilled', 'introducing', 'proud'])
    if has_opening:
        score += 10.0
    
    has_technical_section = any(word in output_lower for word in ['features', 'stack', 'technical', 'capabilities'])
    if has_technical_section:
        score += 10.0
    
    has_closing = any(word in output_lower[-200:] for word in ['thank', 'check out', 'available', 'repo'])
    if has_closing:
        score += 10.0
    
    # Content quality (40 points)
    # Hashtags (10 pts)
    hashtag_count = output.count('#')
    if hashtag_count >= 5:
        score += 10.0
    elif hashtag_count >= 3:
        score += 7.0
    elif hashtag_count >= 1:
        score += 4.0
    
    # Emojis (10 pts) - taste ful engagement
    emoji_indicators = ['🤖', '🎯', '✨', '🚀', '💡', '📊', '🔍']
    emoji_count = sum(1 for emoji in emoji_indicators if emoji in output)
    if emoji_count >= 2:
        score += 10.0
    elif emoji_count >= 1:
        score += 5.0
    
    # Technical specifics (20 pts)
    tech_terms = ['langgraph', 'langchain', 'azure', 'openai', 'gpt', 'rag', 'agent']
    tech_count = sum(1 for term in tech_terms if term in output_lower)
    if tech_count >= 4:
        score += 20.0
    elif tech_count >= 2:
        score += 15.0
    elif tech_count >= 1:
        score += 10.0
    
    # Accuracy & context (30 points)
    # Based on repo data (15 pts)
    has_numbers = any(c.isdigit() for c in output)  # Stats like "25 dependencies"
    if has_numbers:
        score += 15.0
    
    # Self-reflection demonstration (15 pts)
    has_reflection_note = "p.s." in output_lower or "self-reflection" in output_lower
    if has_reflection_note:
        score += 15.0
    
    return min(score, 100.0)


def _evaluate_repository_analysis_quality(state: AgentState) -> float:
    """
    Evaluate output quality for repository analysis reports.
    
    CEO REQUIREMENTS - EVIDENCE-ONLY SCORING:
    - Evidence tags [evidence: ...] MANDATORY for all claims
    - Concrete code references with line numbers
    - Test file citations (tests/test_x.py::test_feature)
    - Dependency versions (package==1.2.3)
    - Actual metrics from command outputs
    - HEAVY penalties for vague language or missing evidence
    """
    output = state.get("final_output", "")
    output_lower = output.lower()
    score = 0.0
    import re
    
    # 🔥 CEO REQUIREMENT: Evidence tags MANDATORY (30 points)
    # Count [evidence: ...] tags
    evidence_tags = re.findall(r'\[evidence:\s*[^\]]+\]', output)
    evidence_count = len(evidence_tags)
    
    if evidence_count >= 15:
        score += 30.0  # Excellent - many evidence tags
    elif evidence_count >= 10:
        score += 25.0  # Good
    elif evidence_count >= 5:
        score += 15.0  # Acceptable
    elif evidence_count >= 1:
        score += 5.0   # Minimal effort
    else:
        score -= 20.0  # PENALTY: No evidence tags at all!
    
    # Completeness (25 points)
    required_sections = ['overview', 'architecture', 'dependencies', 'structure', 'capabilities']
    sections_found = sum(1 for section in required_sections if section in output_lower)
    score += sections_found * 5.0  # 5 points per section
    
    # EVIDENCE-BASED ACCURACY (30 points) - STRICTER
    
    # Concrete code symbols with line numbers (10 pts)
    has_line_refs = bool(re.search(r':(\d+)(?:-\d+)?', output))  # file.py:45 or file.py:45-67
    has_class_refs = bool(re.search(r'`[A-Z][a-zA-Z]+(?:Class|Node|Manager|Runner|Handler)?`', output))
    has_function_refs = bool(re.search(r'`[a-z_]+\(\)`', output))
    
    if has_line_refs and (has_class_refs or has_function_refs):
        score += 10.0  # Line numbers + symbols
    elif has_class_refs and has_function_refs:
        score += 7.0   # Both types but no line numbers
    elif has_class_refs or has_function_refs:
        score += 4.0   # At least one type
    
    # Test file references with :: syntax (10 pts)
    has_test_syntax = "::" in output and "test" in output_lower
    has_test_files = "tests/" in output_lower or "test_" in output_lower
    
    if has_test_syntax and has_test_files:
        score += 10.0  # Proper test citations with ::
    elif has_test_files:
        score += 4.0   # Only test files, no :: syntax
    
    # Dependency versions (5 pts)
    has_versions = "==" in output or "~=" in output
    if has_versions:
        score += 5.0
    
    # Actual command outputs cited (5 pts)
    command_keywords = ['pytest', 'coverage', 'find tests', 'command']
    has_command_ref = any(kw in output_lower for kw in command_keywords)
    if has_command_ref:
        score += 5.0
    
    # PENALIZE VAGUE LANGUAGE (-15 pts max) - HARSHER
    vague_terms = ['likely', 'suggests', 'appears to', 'may', 'probably', 'seems to', 'possibly']
    vague_count = sum(1 for term in vague_terms if term in output_lower)
    
    if vague_count >= 5:
        score -= 15.0  # HEAVY penalty for excessive vagueness
    elif vague_count >= 3:
        score -= 10.0  # Moderate penalty
    elif vague_count >= 1:
        score -= 5.0   # Minor penalty
    
    # Structure & formatting (15 points)
    has_markdown = "#" in output[:100] or "##" in output
    if has_markdown:
        score += 7.0
    
    has_lists = "- " in output or "* " in output or output.count("\n") >= 10
    if has_lists:
        score += 8.0
    
    # Self-reflection section (10 points)
    has_reflection_section, reflection_score = _check_reflection_incorporated(state)
    score += min(reflection_score, 10.0)
    
    return max(0.0, min(score, 100.0))  # Ensure score doesn't go negative


def _evaluate_general_quality(state: AgentState) -> float:
    """
    Evaluate output quality for general queries.
    
    Basic quality checks:
    - Appropriate length
    - Clear structure
    - Addresses the question
    """
    output = state.get("final_output", "")
    score = 0.0
    
    # Base score for having output
    if not output:
        return 0.0
    score += 40.0
    
    # Length appropriateness (30 pts)
    output_length = len(output)
    if 100 <= output_length <= 2000:
        score += 30.0
    elif output_length >= 50:
        score += 20.0
    
    # Structure (30 pts)
    has_structure = output.count("\n") >= 2 or "." in output
    if has_structure:
        score += 20.0
    
    # Self-reflection if present
    has_reflection_section, reflection_score = _check_reflection_incorporated(state)
    if has_reflection_section:
        score += 10.0
    
    return min(score, 100.0)


def calculate_output_quality_score(state: AgentState) -> float:
    """
    Calculate output quality score (0-100) with task-aware evaluation.
    
    Uses specialized evaluation logic based on output type:
    - Code questions: File paths, line numbers, code excerpts, reflection
    - LinkedIn posts: Structure, hashtags, engagement, technical content
    - Repository analysis: Completeness, accuracy, formatting
    - General: Basic quality and structure
    
    Args:
        state: Agent state to evaluate
    
    Returns:
        float: Score from 0-100
    
    Example:
        >>> state = {"task": "Where is X used?", "final_output": "X is in file.py line 10"}
        >>> calculate_output_quality_score(state)
        90.0
    """
    final_output = state.get("final_output", "")
    
    if not final_output:
        return 0.0
    
    # Detect output type and use appropriate evaluator
    output_type = _detect_output_type(state)
    
    if output_type == "code_question":
        return _evaluate_code_question_quality(state)
    elif output_type == "linkedin_post":
        return _evaluate_linkedin_post_quality(state)
    elif output_type == "repository_analysis":
        return _evaluate_repository_analysis_quality(state)
    else:
        return _evaluate_general_quality(state)


def calculate_overall_score(scores: Dict[str, float]) -> float:
    """
    Calculate overall weighted score.
    
    Combines individual metric scores with appropriate weights.
    
    Args:
        scores: Dictionary of individual metric scores
    
    Returns:
        float: Overall score from 0-100
    
    Example:
        >>> scores = {"task_completion": 90, "reasoning_quality": 80}
        >>> calculate_overall_score(scores)
        85.0
    """
    weights = {
        "task_completion": 0.35,
        "reasoning_quality": 0.25,
        "tool_effectiveness": 0.15,
        "reflection_quality": 0.10,
        "output_quality": 0.15
    }
    
    weighted_sum = 0.0
    total_weight = 0.0
    
    for metric, weight in weights.items():
        if metric in scores:
            weighted_sum += scores[metric] * weight
            total_weight += weight
    
    if total_weight == 0:
        return 0.0
    
    return weighted_sum / total_weight
