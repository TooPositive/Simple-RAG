"""
Reasoning node for chain-of-thought processing.

This node performs multi-step reasoning about the task using LLM.
"""

from src.agent.state import AgentState
from openai import AsyncAzureOpenAI
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def reasoning_node(state: AgentState) -> AgentState:
    """
    Perform chain-of-thought reasoning using LLM.

    Args:
        state: Current agent state

    Returns:
        AgentState: Updated state with reasoning
    """
    new_state = dict(state)

    # Check if reasoning should be skipped (for trivial queries)
    skip_reasoning = state.get("skip_reasoning", False)
    if skip_reasoning:
        print("  ⚡ Reasoning skipped (simple query - saves ~1500 tokens)")
        new_state["reasoning_steps"] = state["reasoning_steps"] + [
            "Reasoning: Direct response (no complex reasoning needed)"
        ]
        new_state["next_action"] = "generate"
        return new_state

    # Get LLM client - check if credentials available
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if not api_key:
        print("  ⚠️ No Azure OpenAI credentials found, using fallback reasoning")
        new_state["reasoning_steps"] = state["reasoning_steps"] + [
            "Reasoning: Analyzing available information",
            "Reasoning: Formulating response"
        ]
        new_state["next_action"] = "generate"
        return new_state
    
    client = AsyncAzureOpenAI(
        api_key=api_key,
        api_version=os.getenv("OPENAI_API_VERSION", "2023-12-01-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    
    # Build context from state
    task = state["task"]
    task_type = state.get("task_type", "general")
    repo_structure = state.get("repo_structure", {})
    dependencies = state.get("dependencies", {})
    architecture = state.get("architecture", {})
    
    # Create reasoning prompt
    context = f"Task: {task}\nTask Type: {task_type}\n\n"
    
    if repo_structure:
        context += f"Repository has {len(repo_structure.get('children', []))} items.\n"
    if dependencies:
        deps_list = dependencies.get('dependencies', [])
        context += f"Found {len(deps_list)} dependencies.\n"
    if architecture:
        modules = architecture.get('modules', [])
        context += f"Identified {len(modules)} modules.\n"
    
    prompt = f"""{context}

Analyze this task and provide step-by-step reasoning about how to approach it.
Consider what information is available and what response would be most helpful.

Respond with 3-5 clear reasoning steps in JSON format:
{{
    "reasoning_steps": ["step 1", "step 2", "step 3"]
}}"""
    
    # Retry logic for rate limiting
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print("🧠 Performing LLM-based reasoning...")
            response = await client.chat.completions.create(
                model=os.getenv("LLM_MODEL_NAME", "gpt-4o"),
                messages=[
                    {"role": "system", "content": "You are an analytical AI that provides clear step-by-step reasoning."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            # Try to parse JSON
            try:
                parsed = json.loads(content)
                steps = parsed.get("reasoning_steps", [])
            except:
                # Fallback if not JSON
                steps = [content]
            
            new_state["reasoning_steps"] = state["reasoning_steps"] + [f"Reasoning: {step}" for step in steps]
            print(f"  ✓ Generated {len(steps)} reasoning steps")
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
                print(f"  ⚠️ LLM reasoning failed: {e}, using fallback")
                new_state["reasoning_steps"] = state["reasoning_steps"] + [
                    "Reasoning: Analyzing available information",
                    "Reasoning: Formulating response"
                ]
                break
    
    new_state["next_action"] = "generate"
    
    return new_state
