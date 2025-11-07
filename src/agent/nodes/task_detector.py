"""
Task type detection module.

This module detects task types from user queries to route
them to appropriate prompt templates and handlers.
"""

from typing import Tuple
from src.agent.state import AgentState
from src.agent.nodes.config import KeywordConfig, TaskType


class TaskDetector:
    """
    Detects task type from user query and agent state.

    This makes task classification extensible and testable.
    """

    def __init__(self, keyword_config: KeywordConfig = None):
        """
        Initialize task detector.

        Args:
            keyword_config: Keyword configuration for detection
        """
        self.config = keyword_config or KeywordConfig()

    def detect(self, task: str, state: AgentState) -> Tuple[TaskType, str]:
        """
        Detect task type from query and state.

        Args:
            task: User query/task
            state: Current agent state

        Returns:
            Tuple of (TaskType enum, string representation)
        """
        task_lower = task.lower()

        # Check explicit task type from state
        state_task_type = state.get("task_type", "general")

        # LinkedIn post detection
        if self._matches_keywords(task_lower, self.config.linkedin_keywords):
            return TaskType.LINKEDIN_POST, "linkedin_post"

        # Repository analysis detection
        if state_task_type == "analyze_repo":
            # Check if it's actually a code question
            if self._is_code_question(task_lower):
                return TaskType.CODE_QUESTION, "code_question"
            return TaskType.ANALYZE_REPO, "analyze_repo"

        # Code question detection
        if self._is_code_question(task_lower):
            # Only if we have code files available
            if state.get("code_files"):
                return TaskType.CODE_QUESTION, "code_question"

        # Explanation detection
        if self._matches_keywords(task_lower, self.config.explanation_keywords):
            return TaskType.EXPLAIN, "explain"

        # Default to general
        return TaskType.GENERAL, "general"

    def _is_code_question(self, task_lower: str) -> bool:
        """Check if task is a code-specific question."""
        return self._matches_keywords(task_lower, self.config.code_question_keywords)

    def _matches_keywords(self, text: str, keywords: list) -> bool:
        """Check if text contains any of the keywords."""
        return any(keyword in text for keyword in keywords)

    def should_include_code_context(
        self,
        task: str,
        task_type: TaskType,
        state: AgentState
    ) -> bool:
        """
        Determine if code context should be included.

        Args:
            task: User query
            task_type: Detected task type
            state: Agent state

        Returns:
            True if code context should be included
        """
        if task_type == TaskType.CODE_QUESTION:
            return bool(state.get("code_files"))

        if task_type == TaskType.ANALYZE_REPO:
            return self._is_code_question(task.lower())

        return False
