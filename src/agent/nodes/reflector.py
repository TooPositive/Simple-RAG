"""
Reflection node for self-critique and improvement - Production Quality Refactored Version.

This module provides self-reflection capabilities for the agent using LLM.
Refactored to use modular components and eliminate code duplication.
"""

import json
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

from src.agent.state import AgentState
from src.agent.nodes.config import GeneratorConfig, DEFAULT_CONFIG
from src.agent.nodes.llm_client import LLMClient, LLMResponse
from src.agent.nodes.prompt_templates import PromptBuilder
from src.agent.nodes.exceptions import LLMConnectionError, ConfigurationError

# Load environment variables
load_dotenv()


class ReflectionResult:
    """Container for reflection analysis results."""

    def __init__(
        self,
        assessment: str,
        critique: str,
        next_action: str,
        can_improve_without_data: bool = True
    ):
        self.assessment = assessment
        self.critique = critique
        next_action = next_action
        self.can_improve_without_data = can_improve_without_data


class SelfReflector:
    """
    Production-quality self-reflection system.

    This class provides AI self-critique capabilities,
    designed to be reusable and testable.
    """

    def __init__(
        self,
        config: Optional[GeneratorConfig] = None,
        llm_client: Optional[LLMClient] = None,
        prompt_builder: Optional[PromptBuilder] = None
    ):
        """
        Initialize the self-reflector.

        Args:
            config: Generator configuration (uses default if None)
            llm_client: LLM client instance (creates new if None)
            prompt_builder: Prompt builder instance (creates new if None)
        """
        self.config = config or DEFAULT_CONFIG

        # Initialize components with dependency injection
        try:
            self.llm_client = llm_client or LLMClient(config=self.config.llm)
        except ConfigurationError:
            # If LLM not available, we'll use fallback
            self.llm_client = None

        self.prompt_builder = prompt_builder or PromptBuilder()

    async def reflect(self, state: AgentState) -> ReflectionResult:
        """
        Perform self-reflection on generated output.

        Args:
            state: Current agent state with final_output

        Returns:
            ReflectionResult with assessment and next action

        Raises:
            None - always returns a result (uses fallback if needed)
        """
        task = state["task"]
        task_type = state.get("task_type", "general")
        final_output = state.get("final_output", "")
        reasoning_steps = state.get("reasoning_steps", [])
        tool_usage = state.get("tool_usage", [])
        generation_count = state.get("generation_count", 0)

        # Check if reflection should be skipped
        if state.get("skip_reflection", False):
            print("  ⚡ Self-reflection skipped (simple query - saves ~2500 tokens)")
            return ReflectionResult(
                assessment="good",
                critique="Reflection: Skipped for simple query type",
                next_action="end"
            )

        # Check if max generations reached
        if generation_count >= self.config.reflection.max_generations:
            print(f"  ⚠️  Max generations ({self.config.reflection.max_generations}) reached - accepting current output")
            return ReflectionResult(
                assessment="good",
                critique="Max generation attempts reached, proceeding with current output",
                next_action="end"
            )

        # Try LLM-based reflection if available
        if self.llm_client and self.llm_client.is_available() and final_output:
            try:
                return await self._llm_reflection(
                    task=task,
                    task_type=task_type,
                    final_output=final_output,
                    reasoning_steps=reasoning_steps,
                    tool_usage=tool_usage,
                    generation_count=generation_count
                )
            except Exception as e:
                print(f"  ⚠️ Reflection failed: {e}, using fallback")
                return self._fallback_reflection()
        else:
            return self._fallback_reflection()

    async def _llm_reflection(
        self,
        task: str,
        task_type: str,
        final_output: str,
        reasoning_steps: list,
        tool_usage: list,
        generation_count: int
    ) -> ReflectionResult:
        """
        Perform LLM-based reflection.

        Args:
            task: User task
            task_type: Type of task
            final_output: Generated output to reflect on
            reasoning_steps: Reasoning steps taken
            tool_usage: Tools used
            generation_count: Current generation attempt

        Returns:
            ReflectionResult
        """
        print("🔍 Performing self-reflection on generated output...")

        # Build reflection prompt
        prompt_template = self.prompt_builder.build_reflection_prompt(task_type)

        # Build context for reflection
        context = f"""Task: {task}

Your Generated Output (first 1500 chars):
{final_output[:1500]}

Data Context:
- Reasoning steps: {len(reasoning_steps)}
- Tools called: {len(tool_usage)}
- Generation attempt: {generation_count}
"""

        # Get LLM assessment
        try:
            response = await self.llm_client.generate(
                system_prompt=prompt_template.system,
                user_prompt=context,
                temperature=self.config.reflection.temperature,
                max_tokens=self.config.reflection.max_tokens
            )

            # Parse JSON response
            reflection_data = self._parse_reflection_response(response.content)

            # Log reflection
            print(f"  ✓ Self-assessment: {reflection_data['assessment']}")
            print(f"  💭 Reasoning: {reflection_data['critique']}")

            # Determine next action
            next_action = self._determine_next_action(reflection_data)
            self._log_next_action(next_action, reflection_data)

            return ReflectionResult(
                assessment=reflection_data["assessment"],
                critique=reflection_data["critique"],
                next_action=next_action,
                can_improve_without_data=reflection_data.get("can_improve_without_data", True)
            )

        except LLMConnectionError as e:
            print(f"  ⚠️ LLM reflection failed: {e}")
            return self._fallback_reflection()

    def _parse_reflection_response(self, content: str) -> Dict:
        """
        Parse reflection LLM response.

        Args:
            content: LLM response content

        Returns:
            Dict with assessment, critique, and next_action
        """
        try:
            reflection = json.loads(content)
            return {
                "assessment": reflection.get("assessment", "good"),
                "critique": reflection.get("critique", "Output appears complete"),
                "next_action": reflection.get("next_action", "end"),
                "can_improve_without_data": reflection.get("can_improve_without_data", True)
            }
        except json.JSONDecodeError:
            # Fallback if not JSON
            return {
                "assessment": "good",
                "critique": content[:200],
                "next_action": "end",
                "can_improve_without_data": True
            }

    def _determine_next_action(self, reflection_data: Dict) -> str:
        """
        Determine next action based on reflection assessment.

        Args:
            reflection_data: Parsed reflection data

        Returns:
            Next action string ("end", "retry", or "continue")
        """
        assessment = reflection_data["assessment"]
        can_improve = reflection_data.get("can_improve_without_data", True)

        if assessment == "needs_more_data" and not can_improve:
            return "continue"  # Go back to tools
        elif assessment == "needs_improvement" and can_improve:
            return "retry"  # Regenerate with improvements
        elif assessment == "good":
            return "end"  # Proceed to evaluation
        else:
            # Default: accept current output (prevent loops)
            return "end"

    def _log_next_action(self, next_action: str, reflection_data: Dict):
        """Log the determined next action."""
        if next_action == "continue":
            print(f"  🔄 Action: Requesting more tools/file reads")
            print(f"  📋 Reason: Cannot improve without reading actual file contents")
        elif next_action == "retry":
            print(f"  🔄 Action: Regenerating with better formatting")
        elif next_action == "end":
            print(f"  ✅ Action: Output quality is good, proceeding to evaluation")
        else:
            print(f"  ⚠️  Unclear improvement path - accepting current output")

    def _fallback_reflection(self) -> ReflectionResult:
        """
        Provide fallback reflection when LLM is unavailable.

        Returns:
            ReflectionResult with default "good" assessment
        """
        print("  ✅ Reflection fallback: Proceeding to evaluation")
        return ReflectionResult(
            assessment="good",
            critique="Output appears complete (fallback assessment)",
            next_action="end"
        )


async def reflection_node(state: AgentState) -> AgentState:
    """
    Reflection node for LangGraph workflow.

    This is the entry point called by the LangGraph orchestrator.
    It maintains backward compatibility with the existing system.

    Args:
        state: Current agent state with final_output

    Returns:
        Updated agent state with reflection and next action
    """
    new_state = dict(state)

    # Create reflector (can be configured via state if needed)
    config = state.get("generator_config", DEFAULT_CONFIG)
    reflector = SelfReflector(config=config)

    # Perform reflection
    try:
        result = await reflector.reflect(state)

        # Update state with reflection results
        generation_count = state.get("generation_count", 0)
        reflection_note = f"Reflection (gen {generation_count}): {result.assessment} - {result.critique}"

        new_state["reflection_notes"] = state.get("reflection_notes", []) + [reflection_note]
        new_state["reflection_assessment"] = result.assessment
        new_state["next_action"] = result.next_action

    except Exception as e:
        # Should never happen due to fallback, but just in case
        print(f"  ❌ Reflection node failed: {e}")
        generation_count = state.get("generation_count", 0)
        new_state["reflection_notes"] = state.get("reflection_notes", []) + [
            f"Reflection (gen {generation_count}): Output accepted (error fallback)"
        ]
        new_state["reflection_assessment"] = "good"
        new_state["next_action"] = "end"

    return new_state
