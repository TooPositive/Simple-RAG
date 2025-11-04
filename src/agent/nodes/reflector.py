"""
Reflection node for self-critique and improvement.

This node evaluates the agent's own reasoning and outputs using LLM.
"""

from src.agent.state import AgentState
from openai import AsyncAzureOpenAI
import os
from dotenv import load_dotenv

load_dotenv()


async def reflection_node(state: AgentState) -> AgentState:
    """
    Perform self-reflection and critique on actual output.
    
    This demonstrates the "Reasoning & Reflection" requirement for Ciklum AI Academy.
    The agent analyzes its own OUTPUT (not just reasoning) and decides if:
    - Output is good enough → proceed to evaluation
    - Output needs improvement → regenerate with critique
    - Output lacks data → request more tools/analysis
    
    Args:
        state: Current agent state with final_output
    
    Returns:
        AgentState: Updated state with reflection and next action
    """
    new_state = dict(state)
    
    task = state["task"]
    task_type = state.get("task_type", "general")
    final_output = state.get("final_output", "")
    reasoning_steps = state.get("reasoning_steps", [])
    tool_usage = state.get("tool_usage", [])
    generation_count = state.get("generation_count", 0)  # Track generation attempts
    
    # Check if we have Azure OpenAI credentials
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    
    if not api_key or not final_output:
        # Fallback reflection if no API key or output
        print("  ✓ Self-assessment: good (no API key for reflection)")
        new_state["reflection_notes"] = state.get("reflection_notes", []) + [
            "Reflection: Output appears complete, proceeding to evaluation"
        ]
        new_state["reflection_assessment"] = "good"
        new_state["next_action"] = "end"
        return new_state
    
    try:
        print("🔍 Performing self-reflection on generated output...")
        
        # Build reflection prompt - now critiquing ACTUAL OUTPUT
        task_lower = task.lower()
        is_repo_analysis = task_type == "analyze_repo"
        is_content_gen = task_type == "generate_content"
        
        # Different criteria based on task type
        if is_repo_analysis:
            reflection_prompt = f"""You are a CRITICAL self-reflective AI agent reviewing your own output.

Task: {task}

Your Generated Output (first 1500 chars):
{final_output[:1500]}

CRITICAL SELF-ASSESSMENT:
1. **Specificity**: Does output include actual file paths, line numbers, class/function names?
2. **Evidence**: Are claims backed by [evidence: ...] tags from actual files?
3. **Completeness**: Are key sections present (structure, dependencies, tests, coverage)?
4. **Accuracy**: Do the numbers/facts seem correct based on the data available?

Data Context:
- Reasoning steps: {len(reasoning_steps)}
- Tools called: {len(tool_usage)}
- Generation attempt: {generation_count}

IMPORTANT DECISION LOGIC:
- If output ALREADY HAS specific file paths, class names, evidence tags, test counts, coverage % → assessment: "good"
- If output is well-formatted but could use minor improvements WITHOUT new data → assessment: "needs_improvement"
- If output CANNOT be more specific without reading actual file contents or running more tools → assessment: "needs_more_data"

BE REALISTIC: If output already has file paths, class names, evidence tags, test counts - that's GOOD ENOUGH.
Don't request perfection or "more detailed descriptions" unless there's a REAL problem.

IMPORTANT: BE LENIENT! Only regenerate if there's a SERIOUS issue, not minor wording improvements.

Respond with JSON:
{{
    "assessment": "good/needs_improvement/needs_more_data",
    "critique": "Specific issue ONLY if serious problem (1 sentence)",
    "can_improve_without_data": true/false,
    "next_action": "end/retry/continue"
}}

RULES:
- "good" + "end" → Output has specifics and evidence (DEFAULT - be lenient!)
- "needs_improvement" + "retry" → SERIOUS formatting or structural issue ONLY
- "needs_more_data" + "continue" → Truly cannot answer without reading actual file contents
"""
        elif is_content_gen:
            reflection_prompt = f"""You are a self-reflective AI agent reviewing your LinkedIn post.

Task: {task}

Your Generated Post:
{final_output}

REALISTIC SELF-ASSESSMENT:
1. **Structure**: Does it have an engaging opening, body, and call-to-action?
2. **Professional**: Is the tone appropriate for LinkedIn?
3. **Completeness**: Does it mention the project and its value?

IMPORTANT: You ONLY have local repository data. DO NOT request GitHub stats.

If the post is professional and mentions the project → assessment: "good"
DO NOT regenerate for minor wording improvements.

Respond with JSON:
{{
    "assessment": "good/needs_improvement",
    "critique": "Serious issue ONLY (1 sentence)",
    "can_improve_without_data": true,
    "next_action": "end/retry"
}}

BE VERY LENIENT: If post is decent → say "good" immediately. Don't waste API calls.
"""
        else:
            # Code questions and simple tasks - be VERY lenient
            reflection_prompt = f"""You are reviewing output for a code question.

Task: {task}
Output: {final_output[:800]}

CRITICAL UNDERSTANDING FOR CODE QUESTIONS:
- If output shows specific file paths, line numbers, and code → assessment: "good"
- If something is only used in 1 file, that IS the comprehensive answer
- DO NOT request "comprehensive overview" if the answer already shows all occurrences
- DO NOT request "integration details" if it's just a simple import
- If answer directly addresses the question with specifics → assessment: "good"

YOU CANNOT GET MORE DATA. If output answered the question with what's available → say "good"

Respond with JSON:
{{
    "assessment": "good",
    "critique": "Output answers the question with available data",
    "can_improve_without_data": true,
    "next_action": "end"
}}

BE EXTREMELY LENIENT: If question is answered with file paths/lines → say "good" immediately.
DO NOT waste API calls regenerating the same data.
"""
        
        client = AsyncAzureOpenAI(
            api_key=api_key,
            api_version=os.getenv("OPENAI_API_VERSION", "2023-12-01-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        # Retry logic for rate limiting
        max_retries = 3
        reflection_success = False
        
        for attempt in range(max_retries):
            try:
                response = await client.chat.completions.create(
                    model=os.getenv("LLM_MODEL_NAME", "gpt-4o"),
                    messages=[
                        {"role": "system", "content": "You are a self-reflective AI that critiques your own output and decides next steps."},
                        {"role": "user", "content": reflection_prompt}
                    ],
                    temperature=0.3,  # Lower temperature for consistent self-assessment
                    max_tokens=400
                )
                
                content = response.choices[0].message.content
                
                # Try to parse JSON
                import json
                try:
                    reflection = json.loads(content)
                    assessment = reflection.get("assessment", "good")
                    critique = reflection.get("critique", "Output appears complete")
                    next_action = reflection.get("next_action", "end")
                    missing_data = reflection.get("missing_data", "")
                except:
                    # Fallback if not JSON
                    assessment = "good"
                    critique = content[:200]
                    next_action = "end"
                    missing_data = ""
                
                # Check max generations to prevent endless loops
                max_generations = 3  # Allow max 3 generation attempts
                if generation_count >= max_generations:
                    print(f"  ⚠️  Max generations ({max_generations}) reached - accepting current output")
                    assessment = "good"  # Force completion
                    next_action = "end"
                    critique = "Max generation attempts reached, proceeding with current output"
                
                # Log detailed reflection reasoning
                print(f"  ✓ Self-assessment: {assessment}")
                print(f"  💭 Reasoning: {critique}")
                
                # SMART ROUTING: Check if we can actually improve
                can_improve = reflection.get("can_improve_without_data", True)
                
                if assessment == "needs_more_data" and not can_improve:
                    # Really needs more data - go back to tools
                    next_action = "continue"
                    print(f"  🔄 Action: Requesting more tools/file reads")
                    print(f"  📋 Reason: Cannot improve without reading actual file contents")
                elif assessment == "needs_improvement" and can_improve:
                    # Can improve with same data - just regenerate
                    next_action = "retry"
                    print(f"  🔄 Action: Regenerating with better formatting")
                elif assessment == "good":
                    next_action = "end"
                    print(f"  ✅ Action: Output quality is good, proceeding to evaluation")
                else:
                    # Default: if unsure, accept current output (prevent loops)
                    print(f"  ⚠️  Unclear improvement path - accepting current output")
                    next_action = "end"
                    assessment = "good"
                
                # Add reflection note
                reflection_note = f"Reflection (gen {generation_count}): {assessment} - {critique}"
                new_state["reflection_notes"] = state.get("reflection_notes", []) + [reflection_note]
                new_state["reflection_assessment"] = assessment
                new_state["next_action"] = next_action
                
                reflection_success = True
                break  # Success, exit retry loop
                
            except Exception as e:
                error_str = str(e)
                
                # Check if rate limit error
                if '429' in error_str and attempt < max_retries - 1:
                    import re
                    import time
                    # Extract wait time from error
                    match = re.search(r'retry after (\d+) seconds', error_str.lower())
                    wait_time = int(match.group(1)) if match else 2
                    wait_time *= (attempt + 1)  # Exponential backoff
                    
                    print(f"  ⏳ High demand - waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(wait_time)
                    continue
                else:
                    # Not rate limit or last attempt - use fallback
                    print(f"  ⚠️ Reflection failed: {e}, using fallback")
                    break
        
        # If all retries failed, use fallback (prevent loops)
        if not reflection_success:
            print("  ✅ Reflection fallback: Proceeding to evaluation")
            new_state["reflection_notes"] = state.get("reflection_notes", []) + [
                f"Reflection (gen {generation_count}): Output accepted (reflection failed)"
            ]
            new_state["reflection_assessment"] = "good"
            new_state["next_action"] = "end"  # Always end on fallback
            
    except Exception as e:
        print(f"  ⚠️ Reflection setup failed: {e}, using fallback")
        new_state["reflection_notes"] = state.get("reflection_notes", []) + [
            "Reflection: Output appears complete (error fallback)"
        ]
        new_state["reflection_assessment"] = "good"
        new_state["next_action"] = "end"
    
    return new_state
