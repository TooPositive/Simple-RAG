# src/config.py
"""
Configuration Module for RAG Chatbot

This module manages all configuration and environment variables required by the application.
It uses python-dotenv to load variables from a .env file and validates that all required
settings are present. This ensures that the application fails fast with clear error messages
if configuration is missing or invalid.

Key Responsibilities:
- Load environment variables from .env file
- Validate that all required credentials are present
- Provide a singleton Settings object for use throughout the application
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
# This must happen before the Settings class is instantiated
load_dotenv()


class Settings:
    """
    Application settings loaded from environment variables.

    This class loads and validates all required configuration on initialization.
    If any required environment variable is missing, it raises a ValueError
    immediately, preventing the application from starting in an invalid state.

    Attributes:
        azure_openai_api_key (str): Azure OpenAI API key for authentication
        azure_openai_endpoint (str): Azure OpenAI endpoint URL
        openai_api_version (str): API version to use (e.g., "2023-07-01-preview")
        embedding_model_name (str): Name of the embedding model deployment
        llm_model_name (str): Name of the LLM model deployment (must support Vision for PDF processing)
    """

    def __init__(self):
        # Azure OpenAI API settings - required for all AI operations
        # These values must be set in the .env file
        self.azure_openai_api_key = self._get_env_variable("AZURE_OPENAI_API_KEY")
        self.azure_openai_endpoint = self._get_env_variable("AZURE_OPENAI_ENDPOINT")
        self.openai_api_version = self._get_env_variable("OPENAI_API_VERSION")

        # Model deployment names
        # These should match your Azure OpenAI deployment names
        # embedding_model_name: Used for converting text to vector embeddings
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-ada-002")

        # llm_model_name: Used for chat completions and vision processing
        # IMPORTANT: Must be a vision-enabled model (e.g., gpt-4o, gpt-4-turbo-vision)
        # for the PDF multi-modal processing to work
        self.llm_model_name = os.getenv("LLM_MODEL_NAME", "gpt-4o")

    def _get_env_variable(self, var_name: str) -> str:
        """
        Retrieves an environment variable or raises an error if it's not found.

        This method enforces that all required configuration is present,
        following the "fail fast" principle. It's better to catch configuration
        issues immediately rather than having the application fail later with
        cryptic errors.

        Args:
            var_name (str): The name of the environment variable to retrieve

        Returns:
            str: The value of the environment variable

        Raises:
            ValueError: If the environment variable is not set
        """
        value = os.getenv(var_name)
        if value is None:
            raise ValueError(
                f"Error: Environment variable '{var_name}' not set. "
                f"Please ensure your .env file contains this variable."
            )
        return value


# Create a singleton instance of Settings
# This instance can be imported and used throughout the application
# Usage: from src.config import settings
settings = Settings()
