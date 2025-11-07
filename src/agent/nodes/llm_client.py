"""
LLM client wrapper for Azure OpenAI.

This module encapsulates all LLM interaction logic, making it
easier to swap LLM providers or mock for testing.
"""

import os
import re
import time
from typing import Optional
from openai import AsyncAzureOpenAI
from dataclasses import dataclass

from src.agent.nodes.config import LLMConfig
from src.agent.nodes.exceptions import (
    LLMConnectionError,
    LLMRateLimitError,
    LLMResponseError,
    ConfigurationError
)


@dataclass
class LLMResponse:
    """Container for LLM response data."""
    content: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None


class LLMClient:
    """
    Wrapper for Azure OpenAI LLM client.

    This class provides a clean interface to LLM services with:
    - Automatic retry logic for rate limits
    - Proper error handling
    - Easy provider swapping
    - Testability through mocking
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        config: Optional[LLMConfig] = None
    ):
        """
        Initialize LLM client.

        Args:
            api_key: Azure OpenAI API key (or from env)
            endpoint: Azure OpenAI endpoint (or from env)
            config: LLM configuration

        Raises:
            ConfigurationError: If required credentials are missing
        """
        self.config = config or LLMConfig()
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")

        if not self.api_key:
            raise ConfigurationError(
                "AZURE_OPENAI_API_KEY not found in environment or parameters"
            )

        if not self.endpoint:
            raise ConfigurationError(
                "AZURE_OPENAI_ENDPOINT not found in environment or parameters"
            )

        self._client: Optional[AsyncAzureOpenAI] = None

    def _get_client(self) -> AsyncAzureOpenAI:
        """Get or create Azure OpenAI client."""
        if self._client is None:
            self._client = AsyncAzureOpenAI(
                api_key=self.api_key,
                api_version=self.config.api_version,
                azure_endpoint=self.endpoint
            )
        return self._client

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        attempt_number: int = 1
    ) -> LLMResponse:
        """
        Generate response from LLM.

        Args:
            system_prompt: System instruction for the LLM
            user_prompt: User query/context
            temperature: Sampling temperature (overrides config if provided)
            max_tokens: Maximum tokens to generate (overrides config if provided)
            attempt_number: Current attempt number (for logging)

        Returns:
            LLMResponse with generated content

        Raises:
            LLMConnectionError: If connection to LLM fails
            LLMRateLimitError: If rate limit is exceeded
            LLMResponseError: If response is invalid or empty
        """
        temp = temperature if temperature is not None else self.config.temperature
        max_tok = max_tokens if max_tokens is not None else self.config.max_tokens

        print(f"  🤖 Generating response (attempt {attempt_number})...")

        for retry in range(self.config.max_retries):
            try:
                client = self._get_client()

                response = await client.chat.completions.create(
                    model=self.config.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temp,
                    max_tokens=max_tok
                )

                content = response.choices[0].message.content

                if not content:
                    raise LLMResponseError("LLM returned empty response")

                return LLMResponse(
                    content=content,
                    model=self.config.model_name,
                    tokens_used=response.usage.total_tokens if response.usage else None,
                    finish_reason=response.choices[0].finish_reason
                )

            except Exception as e:
                error_str = str(e)

                # Check if rate limit error
                if '429' in error_str:
                    if retry < self.config.max_retries - 1:
                        wait_time = self._extract_wait_time(error_str, retry)
                        print(f"  ⏳ High demand - waiting {wait_time}s before retry {retry + 1}/{self.config.max_retries}...")
                        print(f"      This helps ensure fair access for everyone. Thank you for your patience!")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise LLMRateLimitError(
                            f"Rate limit exceeded after {self.config.max_retries} retries",
                            retry_after=wait_time
                        )

                # Check if connection error
                elif any(term in error_str.lower() for term in ['connection', 'timeout', 'network']):
                    if retry < self.config.max_retries - 1:
                        wait_time = self.config.initial_retry_delay * (retry + 1)
                        print(f"  ⚠️ Connection issue - retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise LLMConnectionError(
                            f"Failed to connect to LLM after {self.config.max_retries} retries: {error_str}"
                        )

                # Unknown error
                else:
                    raise LLMConnectionError(f"LLM generation failed: {error_str}")

        # Should never reach here, but just in case
        raise LLMConnectionError("LLM generation failed after all retries")

    def _extract_wait_time(self, error_str: str, retry_count: int) -> int:
        """
        Extract wait time from error message.

        Args:
            error_str: Error message string
            retry_count: Current retry count

        Returns:
            Wait time in seconds (with exponential backoff)
        """
        match = re.search(r'retry after (\d+) seconds', error_str.lower())
        base_wait = int(match.group(1)) if match else self.config.initial_retry_delay
        return base_wait * (retry_count + 1)  # Exponential backoff

    def is_available(self) -> bool:
        """
        Check if LLM client is properly configured.

        Returns:
            True if credentials are available
        """
        return bool(self.api_key and self.endpoint)


class MockLLMClient(LLMClient):
    """
    Mock LLM client for testing.

    This allows testing without actual API calls.
    """

    def __init__(self, mock_response: str = "Mock response"):
        """
        Initialize mock client.

        Args:
            mock_response: Canned response to return
        """
        self.mock_response = mock_response
        self.config = LLMConfig()
        self.api_key = "mock_key"
        self.endpoint = "https://mock.endpoint"

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        attempt_number: int = 1
    ) -> LLMResponse:
        """Return mock response."""
        return LLMResponse(
            content=self.mock_response,
            model="mock-model",
            tokens_used=100,
            finish_reason="stop"
        )

    def is_available(self) -> bool:
        """Mock client is always available."""
        return True