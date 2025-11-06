"""
Content generation node - Production Quality Refactored Version.

This module generates final output using LLM for intelligent responses.
Refactored to be modular, reusable, and easily portable to other projects.
"""

from src.agent.state import AgentState
from typing import Optional
from dotenv import load_dotenv

# Import all our modular components
from src.agent.nodes.config import GeneratorConfig, DEFAULT_CONFIG
from src.agent.nodes.exceptions import (
    GeneratorError,
    LLMConnectionError,
    ConfigurationError
)
from src.agent.nodes.llm_client import LLMClient
from src.agent.nodes.context_builder import ContextBuilder
from src.agent.nodes.prompt_templates import PromptBuilder
from src.agent.nodes.task_detector import TaskDetector
from src.agent.nodes.fallback_generator import FallbackGenerator

# Load environment variables
load_dotenv()


class ContentGenerator:
    """
    Production-quality content generator.

    This class is designed to be:
    - Reusable across different projects
    - Easily testable with dependency injection
    - Configurable through external configuration
    - Extensible for new task types
    """

    def __init__(
        self,
        config: Optional[GeneratorConfig] = None,
        llm_client: Optional[LLMClient] = None,
        context_builder: Optional[ContextBuilder] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        task_detector: Optional[TaskDetector] = None,
        fallback_generator: Optional[FallbackGenerator] = None
    ):
        """
        Initialize the content generator.

        Args:
            config: Generator configuration (uses default if None)
            llm_client: LLM client instance (creates new if None)
            context_builder: Context builder instance (creates new if None)
            prompt_builder: Prompt builder instance (creates new if None)
            task_detector: Task detector instance (creates new if None)
            fallback_generator: Fallback generator instance (creates new if None)
        """
        self.config = config or DEFAULT_CONFIG

        # Initialize components (with dependency injection for testability)
        try:
            self.llm_client = llm_client or LLMClient(config=self.config.llm)
        except ConfigurationError:
            # If LLM not available, we'll use fallback
            self.llm_client = None

        self.context_builder = context_builder or ContextBuilder(self.config.context)
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.task_detector = task_detector or TaskDetector(self.config.keywords)
        self.fallback_generator = fallback_generator or FallbackGenerator(self.config)

    async def generate(self, state: AgentState, include_reflection: bool = True) -> str:
        """
        Generate content based on state.

        This is the main entry point for content generation.

        Args:
            state: Current agent state
            include_reflection: Whether to include reflection notes in context

        Returns:
            Generated content string

        Raises:
            GeneratorError: If generation fails
        """
        task = state["task"]

        # Detect task type
        task_type_enum, task_type_str = self.task_detector.detect(task, state)

        # Build context
        context = self.context_builder.build_context(
            state=state,
            task=task,
            task_type=task_type_str,
            include_reflection=include_reflection
        )

        # Build prompt template
        has_reflection = include_reflection and bool(state.get("reflection_notes"))

        prompt_template = self.prompt_builder.build_prompt(
            task_type=task_type_str,
            has_reflection=has_reflection,
            project_name=self.config.project.project_name,
            organization=self.config.project.organization
        )

        # Generate using LLM or fallback
        try:
            if self.llm_client and self.llm_client.is_available():
                generation_count = state.get("generation_count", 0) + 1
                response = await self.llm_client.generate(
                    system_prompt=prompt_template.system,
                    user_prompt=context,
                    attempt_number=generation_count
                )
                output = response.content
                print(f"  ✓ Generated {len(output)} characters")
                return output

            else:
                print("  ⚠️ No LLM credentials found, using template fallback")
                return self.fallback_generator.generate(state, task_type_str)

        except (LLMConnectionError, Exception) as e:
            print(f"  ⚠️ LLM generation failed: {e}, using fallback")
            if self.config.enable_fallback_templates:
                return self.fallback_generator.generate(state, task_type_str)
            else:
                raise GeneratorError(f"Content generation failed: {e}")


async def generation_node(state: AgentState) -> AgentState:
    """
    Generation node for LangGraph workflow.

    This is the entry point called by the LangGraph orchestrator.
    It maintains backward compatibility with the existing system.

    Args:
        state: Current agent state

    Returns:
        Updated agent state with generated output
    """
    new_state = dict(state)

    # Create generator (can be configured via state if needed)
    config = state.get("generator_config", DEFAULT_CONFIG)
    generator = ContentGenerator(config=config)

    # Generate output
    try:
        output = await generator.generate(state, include_reflection=True)

        # Track generation attempts
        generation_count = state.get("generation_count", 0) + 1
        new_state["generation_count"] = generation_count

        # Set output and completion status
        new_state["final_output"] = output
        new_state["is_complete"] = True

    except GeneratorError as e:
        # Handle generation failure
        print(f"  ❌ Generation failed: {e}")
        new_state["final_output"] = f"Error: Content generation failed. {str(e)}"
        new_state["is_complete"] = False
        new_state["error"] = str(e)

    return new_state


# Legacy function for backward compatibility
async def _generate_with_llm(state: AgentState, include_reflection: bool = True) -> str:
    """
    Legacy function maintained for backward compatibility.

    New code should use ContentGenerator class directly.

    Args:
        state: Agent state with context
        include_reflection: Whether to include reflection notes

    Returns:
        Generated output string
    """
    generator = ContentGenerator()
    return await generator.generate(state, include_reflection)
