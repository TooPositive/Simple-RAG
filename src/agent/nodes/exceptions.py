"""
Custom exceptions for the content generation system.

These exceptions provide better error handling and debugging capabilities.
"""


class GeneratorError(Exception):
    """Base exception for all generator-related errors."""
    pass


class LLMConnectionError(GeneratorError):
    """Raised when connection to LLM service fails."""
    pass


class LLMRateLimitError(GeneratorError):
    """Raised when LLM rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int = 0):
        super().__init__(message)
        self.retry_after = retry_after


class LLMResponseError(GeneratorError):
    """Raised when LLM returns invalid or empty response."""
    pass


class PromptGenerationError(GeneratorError):
    """Raised when prompt generation fails."""
    pass


class ConfigurationError(GeneratorError):
    """Raised when configuration is invalid or missing."""
    pass


class ContextBuildError(GeneratorError):
    """Raised when context building fails."""
    pass
