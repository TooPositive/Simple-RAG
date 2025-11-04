"""
Evaluation explanation generator.

Provides detailed explanations for why each evaluation score was assigned,
making the evaluation transparent and educational.
"""

from typing import Dict, List
from src.agent.state import AgentState
from src.evaluation.metrics import _detect_output_type, _check_reflection_incorporated


def explain_task_completion_score(state: AgentState, score: float) -> List[str]:
    """
    Generate explanation for task completion score.
    
    Args:
        state: Agent state
        score: Calculated score
    
    Returns:
        List[str]: Explanation lines
    """
    explanations = []
    
    # Check what contributed to the score
    if state.get("final_output"):
        explanations.append("✅ Generated final output (50/50 pts)")
    else:
        explanations.append("❌ No final output (0/50 pts)")
    
    if state.get("is_complete"):
        explanations.append("✅ Task marked as complete (30/30 pts)")
    else:
        explanations.append("⚠️  Task not marked complete (0/30 pts)")
    
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 10)
    if iteration_count < max_iterations:
        explanations.append(f"✅ Completed efficiently ({iteration_count}/{max_iterations} iterations, 20/20 pts)")
    elif iteration_count == max_iterations:
        explanations.append(f"⚠️  Used all iterations ({iteration_count}/{max_iterations}, 10/20 pts)")
    else:
        explanations.append(f"❌ Exceeded iteration limit (0/20 pts)")
    
    return explanations


def explain_reasoning_quality_score(state: AgentState, score: float) -> List[str]:
    """
    Generate explanation for reasoning quality score.
    
    Args:
        state: Agent state
        score: Calculated score
    
    Returns:
        List[str]: Explanation lines
    """
    explanations = []
    
    reasoning_steps = state.get("reasoning_steps", [])
    num_steps = len(reasoning_steps)
    
    if num_steps > 0:
        explanations.append(f"✅ Generated {num_steps} reasoning steps (40/40 pts)")
        
        if num_steps >= 5:
            explanations.append("✅ Comprehensive reasoning depth - 5+ steps (40/40 pts)")
        elif num_steps >= 3:
            explanations.append("✅ Adequate reasoning depth - 3-4 steps (30/40 pts)")
        elif num_steps >= 1:
            explanations.append("⚠️  Minimal reasoning depth - 1-2 steps (20/40 pts)")
    else:
        explanations.append("❌ No reasoning steps generated (0/40 pts)")
        explanations.append("❌ No depth analysis possible (0/40 pts)")
    
    reflection_notes = state.get("reflection_notes", [])
    if len(reflection_notes) > 0:
        explanations.append(f"✅ Included self-reflection ({len(reflection_notes)} notes, 20/20 pts)")
    else:
        explanations.append("⚠️  No self-reflection performed (0/20 pts)")
    
    return explanations


def explain_tool_effectiveness_score(state: AgentState, score: float) -> List[str]:
    """
    Generate explanation for tool effectiveness score.
    
    Args:
        state: Agent state
        score: Calculated score
    
    Returns:
        List[str]: Explanation lines
    """
    explanations = []
    
    tool_usage = state.get("tool_usage", [])
    num_tools = len(tool_usage)
    
    if num_tools > 0:
        explanations.append(f"✅ Used {num_tools} tool calls (50/50 pts)")
        
        if num_tools >= 3:
            explanations.append("✅ Multiple diverse tool calls - 3+ (30/30 pts)")
        elif num_tools >= 2:
            explanations.append("✅ Good tool usage - 2 calls (20/30 pts)")
        elif num_tools >= 1:
            explanations.append("⚠️  Minimal tool usage - 1 call (10/30 pts)")
    else:
        explanations.append("⚠️  No tools used (0/50 pts)")
        explanations.append("⚠️  No tool diversity (0/30 pts)")
    
    has_repo_data = state.get("repo_structure") is not None
    has_dependencies = state.get("dependencies") is not None
    
    if has_repo_data and has_dependencies:
        explanations.append("✅ Tools produced comprehensive results (20/20 pts)")
    elif has_repo_data or has_dependencies:
        explanations.append("⚠️  Tools produced partial results (10/20 pts)")
    else:
        explanations.append("⚠️  Tools produced no structured results (0/20 pts)")
    
    return explanations


def explain_reflection_quality_score(state: AgentState, score: float) -> List[str]:
    """
    Generate explanation for reflection quality score.
    
    Args:
        state: Agent state
        score: Calculated score
    
    Returns:
        List[str]: Explanation lines
    """
    explanations = []
    
    reflection_notes = state.get("reflection_notes", [])
    num_notes = len(reflection_notes)
    
    if num_notes > 0:
        explanations.append(f"✅ Generated {num_notes} reflection note(s) (30/30 pts)")
        
        if num_notes >= 3:
            explanations.append("✅ Deep self-critique - 3+ insights (30/30 pts)")
        elif num_notes >= 2:
            explanations.append("✅ Good self-critique - 2 insights (20/30 pts)")
        elif num_notes >= 1:
            explanations.append("⚠️  Basic self-critique - 1 insight (15/30 pts)")
    else:
        explanations.append("❌ No reflection performed (0/30 pts)")
        explanations.append("❌ No critique depth (0/30 pts)")
    
    # Check incorporation (CRITICAL for proof)
    has_reflection_section, incorporation_score = _check_reflection_incorporated(state)
    
    if has_reflection_section:
        output_lower = state.get("final_output", "").lower()
        critique_terms = ['addressing', 'critique', 'mentioned', 'noted', 'responding to']
        references = sum(1 for term in critique_terms if term in output_lower)
        
        if references >= 3:
            explanations.append("✅ STRONG PROOF: Reflection incorporated in output (40/40 pts)")
            explanations.append("   - Has '🔍 How Self-Reflection Improved' section")
            explanations.append(f"   - References critique {references} times (addressing, noted, etc.)")
        elif references >= 1:
            explanations.append("✅ GOOD PROOF: Reflection incorporated (40/40 pts)")
            explanations.append("   - Has reflection improvement section")
            explanations.append(f"   - References critique {references} time(s)")
        else:
            explanations.append("⚠️  WEAK PROOF: Has section but few references (40/40 pts)")
    elif num_notes > 0:
        output_lower = state.get("final_output", "").lower()
        implicit = any(term in output_lower for term in ['addressing', 'improved', 'enhanced'])
        if implicit:
            explanations.append("⚠️  Reflection implicitly addressed (20/40 pts)")
            explanations.append("   - No explicit section, but improvement language present")
        else:
            explanations.append("❌ Reflection NOT incorporated in output (0/40 pts)")
            explanations.append("   - Self-critique generated but not used!")
    
    return explanations


def explain_output_quality_score(state: AgentState, score: float) -> List[str]:
    """
    Generate explanation for output quality score with task-aware details.
    
    Args:
        state: Agent state
        score: Calculated score
    
    Returns:
        List[str]: Explanation lines
    """
    explanations = []
    
    final_output = state.get("final_output", "")
    if not final_output:
        explanations.append("❌ No output generated (0/100 pts)")
        return explanations
    
    # Detect output type
    output_type = _detect_output_type(state)
    output_lower = final_output.lower()
    
    if output_type == "code_question":
        explanations.append("📋 Task Type: CODE QUESTION (specialized evaluation)")
        explanations.append("")
        explanations.append("Specificity Indicators (40 pts):")
        
        # File references
        has_file = ".py" in final_output or "/" in final_output
        if has_file:
            files = [word for word in final_output.split() if ".py" in word]
            explanations.append(f"   ✅ File paths present: {files[0] if files else 'Yes'} (10/10 pts)")
        else:
            explanations.append("   ❌ No file paths (0/10 pts)")
        
        # Line numbers
        has_lines = "line" in output_lower and any(c.isdigit() for c in final_output)
        if has_lines:
            explanations.append("   ✅ Line numbers specified (10/10 pts)")
        else:
            explanations.append("   ❌ No line numbers (0/10 pts)")
        
        # Code excerpts
        has_code = any(word in output_lower for word in ["import", "from", "def", "class"]) or "`" in final_output
        if has_code:
            explanations.append("   ✅ Code excerpts included (10/10 pts)")
        else:
            explanations.append("   ❌ No code excerpts (0/10 pts)")
        
        # Identifiers
        has_identifiers = any(c.isupper() for c in final_output) or "()" in final_output
        if has_identifiers:
            explanations.append("   ✅ Function/class names present (10/10 pts)")
        else:
            explanations.append("   ❌ No identifiers (0/10 pts)")
        
        explanations.append("")
        explanations.append("Completeness (30 pts):")
        
        length = len(final_output)
        if length >= 500:
            explanations.append(f"   ✅ Comprehensive answer ({length} chars, 15/15 pts)")
        elif length >= 200:
            explanations.append(f"   ✅ Adequate length ({length} chars, 12/15 pts)")
        elif length >= 100:
            explanations.append(f"   ⚠️  Minimal length ({length} chars, 8/15 pts)")
        else:
            explanations.append(f"   ❌ Too brief ({length} chars, 0/15 pts)")
        
        has_context = any(word in output_lower for word in ["used in", "function", "purpose"])
        if has_context:
            explanations.append("   ✅ Includes context/explanation (15/15 pts)")
        else:
            explanations.append("   ⚠️  Missing context (0/15 pts)")
        
        # Reflection section
        explanations.append("")
        explanations.append("Self-Reflection Integration (30 pts):")
        has_section, ref_score = _check_reflection_incorporated(state)
        if has_section:
            explanations.append("   ✅ Has '🔍 How Self-Reflection Improved' section (15/15 pts)")
            if ref_score >= 25:
                explanations.append("   ✅ Strong critique references (15/15 pts)")
            else:
                explanations.append("   ⚠️  Weak critique references (10/15 pts)")
        else:
            explanations.append("   ❌ No reflection section (0/30 pts)")
    
    elif output_type == "linkedin_post":
        explanations.append("📋 Task Type: LINKEDIN POST (specialized evaluation)")
        explanations.append("")
        
        # Professional structure
        has_opening = any(word in output_lower[:200] for word in ['excited', 'thrilled', 'introducing'])
        has_features = any(word in output_lower for word in ['features', 'stack', 'capabilities'])
        has_closing = any(word in output_lower[-200:] for word in ['thank', 'check out', 'available'])
        
        explanations.append("Professional Structure (30 pts):")
        explanations.append(f"   {'✅' if has_opening else '❌'} Engaging opening ({10 if has_opening else 0}/10 pts)")
        explanations.append(f"   {'✅' if has_features else '❌'} Technical features section ({10 if has_features else 0}/10 pts)")
        explanations.append(f"   {'✅' if has_closing else '❌'} Call-to-action closing ({10 if has_closing else 0}/10 pts)")
        
        # Content quality
        hashtag_count = final_output.count('#')
        emoji_count = sum(1 for emoji in ['🤖', '🎯', '✨', '🚀'] if emoji in final_output)
        tech_terms = sum(1 for term in ['langgraph', 'azure', 'gpt', 'rag'] if term in output_lower)
        
        explanations.append("")
        explanations.append("Content Quality (40 pts):")
        if hashtag_count >= 5:
            explanations.append(f"   ✅ Excellent hashtag usage ({hashtag_count} hashtags, 10/10 pts)")
        elif hashtag_count >= 3:
            explanations.append(f"   ✅ Good hashtag usage ({hashtag_count} hashtags, 7/10 pts)")
        elif hashtag_count >= 1:
            explanations.append(f"   ⚠️  Minimal hashtags ({hashtag_count}, 4/10 pts)")
        else:
            explanations.append("   ❌ No hashtags (0/10 pts)")
        
        if emoji_count >= 2:
            explanations.append(f"   ✅ Engaging emojis ({emoji_count} types, 10/10 pts)")
        elif emoji_count >= 1:
            explanations.append(f"   ⚠️  Some emojis ({emoji_count}, 5/10 pts)")
        else:
            explanations.append("   ⚠️  No emojis (0/10 pts)")
        
        if tech_terms >= 4:
            explanations.append(f"   ✅ Technical specificity (20/20 pts)")
        elif tech_terms >= 2:
            explanations.append(f"   ✅ Some technical terms (15/20 pts)")
        else:
            explanations.append(f"   ⚠️  Lacks technical details (10/20 pts)")
        
        # Accuracy
        has_numbers = any(c.isdigit() for c in final_output)
        has_reflection = "p.s." in output_lower or "self-reflection" in output_lower
        
        explanations.append("")
        explanations.append("Accuracy & Authenticity (30 pts):")
        explanations.append(f"   {'✅' if has_numbers else '⚠️ '} Repo stats included ({15 if has_numbers else 0}/15 pts)")
        explanations.append(f"   {'✅' if has_reflection else '⚠️ '} Self-reflection demo ({15 if has_reflection else 0}/15 pts)")
    
    elif output_type == "repository_analysis":
        explanations.append("📋 Task Type: REPOSITORY ANALYSIS (specialized evaluation)")
        explanations.append("")
        
        # Completeness
        sections = ['overview', 'architecture', 'dependencies', 'structure', 'capabilities']
        found_sections = [s for s in sections if s in output_lower]
        
        explanations.append("Completeness (40 pts):")
        for section in sections:
            if section in output_lower:
                explanations.append(f"   ✅ Has {section} section (8/8 pts)")
            else:
                explanations.append(f"   ❌ Missing {section} section (0/8 pts)")
        
        # Accuracy
        has_files = ".py" in final_output or ".md" in final_output
        has_structure = "/" in final_output or "src/" in output_lower
        has_deps = "dependencies" in output_lower and any(c.isdigit() for c in final_output)
        
        explanations.append("")
        explanations.append("Accuracy (30 pts):")
        explanations.append(f"   {'✅' if has_files else '❌'} Real file names ({10 if has_files else 0}/10 pts)")
        explanations.append(f"   {'✅' if has_structure else '❌'} Actual structure ({10 if has_structure else 0}/10 pts)")
        explanations.append(f"   {'✅' if has_deps else '❌'} Dependency details ({10 if has_deps else 0}/10 pts)")
        
        # Structure
        has_markdown = "#" in final_output[:100]
        has_lists = "- " in final_output or output_lower.count("\n") >= 10
        
        explanations.append("")
        explanations.append("Structure & Formatting (30 pts):")
        explanations.append(f"   {'✅' if has_markdown else '⚠️ '} Markdown formatting ({10 if has_markdown else 0}/10 pts)")
        explanations.append(f"   {'✅' if has_lists else '⚠️ '} Well-organized lists ({10 if has_lists else 0}/10 pts)")
        
        has_section, _ = _check_reflection_incorporated(state)
        explanations.append(f"   {'✅' if has_section else '⚠️ '} Reflection section ({10 if has_section else 0}/10 pts)")
    
    else:
        explanations.append("📋 Task Type: GENERAL (basic evaluation)")
        length = len(final_output)
        explanations.append(f"   ✅ Has output ({length} chars, 40/40 pts)")
        
        if 100 <= length <= 2000:
            explanations.append(f"   ✅ Appropriate length (30/30 pts)")
        elif length >= 50:
            explanations.append(f"   ⚠️  Length acceptable (20/30 pts)")
        else:
            explanations.append(f"   ⚠️  Too brief (10/30 pts)")
        
        has_structure = output_lower.count("\n") >= 2
        explanations.append(f"   {'✅' if has_structure else '⚠️ '} Has structure ({20 if has_structure else 0}/20 pts)")
        
        has_section, _ = _check_reflection_incorporated(state)
        if has_section:
            explanations.append(f"   ✅ Reflection section (10/10 pts)")
    
    return explanations


def generate_all_explanations(state: AgentState, scores: Dict[str, float]) -> Dict[str, List[str]]:
    """
    Generate explanations for all evaluation scores.
    
    Args:
        state: Agent state
        scores: Calculated scores
    
    Returns:
        Dict[str, List[str]]: Metric name -> list of explanation lines
    """
    return {
        "task_completion": explain_task_completion_score(state, scores.get("task_completion", 0)),
        "reasoning_quality": explain_reasoning_quality_score(state, scores.get("reasoning_quality", 0)),
        "tool_effectiveness": explain_tool_effectiveness_score(state, scores.get("tool_effectiveness", 0)),
        "reflection_quality": explain_reflection_quality_score(state, scores.get("reflection_quality", 0)),
        "output_quality": explain_output_quality_score(state, scores.get("output_quality", 0))
    }
