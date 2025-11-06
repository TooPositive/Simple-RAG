"""
Configuration module for the content generation system.

This module centralizes all configuration values to make the system
easily portable and reusable across different projects.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class TaskType(Enum):
    """Enumeration of supported task types."""
    GENERAL = "general"
    ANALYZE_REPO = "analyze_repo"
    CODE_QUESTION = "code_question"
    LINKEDIN_POST = "linkedin_post"
    EXPLAIN = "explain"


@dataclass
class LLMConfig:
    """Configuration for LLM/OpenAI settings."""
    model_name: str = "gpt-4o"
    api_version: str = "2023-12-01-preview"
    temperature: float = 0.7
    max_tokens: int = 2000
    max_retries: int = 3
    initial_retry_delay: int = 2  # seconds


@dataclass
class ContextConfig:
    """Configuration for context building."""
    max_source_files_to_include: int = 3
    max_import_lines_per_file: int = 10
    max_definitions_per_file: int = 5
    max_code_excerpt_lines: int = 1000
    max_dependencies_to_show: int = 20
    max_modules_to_show: int = 12
    max_classes_to_show: int = 15
    max_functions_to_show: int = 20
    max_tests_to_show: int = 15


@dataclass
class KeywordConfig:
    """Configuration for task detection keywords."""
    code_question_keywords: List[str] = field(default_factory=lambda: [
        'where', 'which file', 'which class', 'how is', 'show me',
        'find', 'locate', 'used in', 'in which', 'implemented',
        'code', 'function', 'class', 'exactly', 'specific', 'import'
    ])

    linkedin_keywords: List[str] = field(default_factory=lambda: [
        'linkedin', 'post', 'social media'
    ])

    explanation_keywords: List[str] = field(default_factory=lambda: [
        'evaluation', 'metric', 'explain', 'how does'
    ])


@dataclass
class ProjectMetadata:
    """
    Project-specific metadata that can be easily changed.

    This allows the system to be reused for different projects
    by simply updating these values.
    """
    project_name: str = "Simple-RAG v2.0"
    project_description: str = "An Autonomous AI Agent System"
    organization: str = "Ciklum AI Academy"

    # Technical stack - can be auto-detected or configured
    key_technologies: List[str] = field(default_factory=lambda: [
        "LangGraph", "LangChain", "Azure OpenAI", "ChromaDB", "GPT-4o"
    ])

    # System capabilities - can be auto-detected or configured
    system_capabilities: List[str] = field(default_factory=lambda: [
        "LangGraph orchestration with intelligent nodes",
        "Autonomous repository analysis capabilities",
        "Multi-step reasoning powered by chain-of-thought",
        "Self-reflection mechanism for quality assurance",
        "Multi-metric evaluation framework"
    ])

    # Social media hashtags
    default_hashtags: List[str] = field(default_factory=lambda: [
        "#AIEngineering", "#AutonomousAI", "#MachineLearning"
    ])

    # Version control
    version: str = "2.0"


@dataclass
class GeneratorConfig:
    """Main configuration container for the generator."""
    llm: LLMConfig = field(default_factory=LLMConfig)
    context: ContextConfig = field(default_factory=ContextConfig)
    keywords: KeywordConfig = field(default_factory=KeywordConfig)
    project: ProjectMetadata = field(default_factory=ProjectMetadata)

    # Feature flags
    enable_reflection: bool = True
    enable_evidence_tags: bool = True
    enable_fallback_templates: bool = True

    # Scoring weights for evaluation
    scoring_weights: Dict[str, float] = field(default_factory=lambda: {
        "task_completion": 0.35,
        "reasoning_quality": 0.25,
        "tool_effectiveness": 0.15,
        "reflection_quality": 0.10,
        "output_quality": 0.15
    })

    @classmethod
    def from_env(cls, **overrides) -> 'GeneratorConfig':
        """
        Create configuration from environment variables with overrides.

        Args:
            **overrides: Keyword arguments to override default values

        Returns:
            GeneratorConfig instance
        """
        import os

        llm_config = LLMConfig(
            model_name=os.getenv("LLM_MODEL_NAME", "gpt-4o"),
            api_version=os.getenv("OPENAI_API_VERSION", "2023-12-01-preview"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "3"))
        )

        config = cls(llm=llm_config)

        # Apply overrides
        for key, value in overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)

        return config

    def update_project_metadata(
        self,
        project_name: Optional[str] = None,
        organization: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Update project metadata dynamically.

        This allows the system to be adapted for different projects.

        Args:
            project_name: Name of the project
            organization: Organization name
            **kwargs: Additional metadata fields
        """
        if project_name:
            self.project.project_name = project_name
        if organization:
            self.project.organization = organization

        for key, value in kwargs.items():
            if hasattr(self.project, key):
                setattr(self.project, key, value)


# Global default configuration instance
DEFAULT_CONFIG = GeneratorConfig()
