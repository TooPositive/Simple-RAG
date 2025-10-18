# tests/test_config.py
"""
Unit tests for the configuration module.

These tests verify that the Settings class correctly loads environment variables
and fails appropriately when required variables are missing. We use pytest's
monkeypatch fixture to temporarily set/unset environment variables during tests,
ensuring tests don't depend on or affect the actual .env file.
"""

import pytest
import os


def test_settings_load_successfully(monkeypatch):
    """
    Tests that settings are loaded correctly when all env vars are present.

    This test uses monkeypatch to temporarily set environment variables,
    then imports the Settings class and verifies it loads them correctly.
    """
    # Use monkeypatch to set environment variables for the duration of this test
    # These will be automatically cleaned up after the test completes
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "fake_key_for_testing")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://fake.endpoint.com/")
    monkeypatch.setenv("OPENAI_API_VERSION", "2023-12-01-preview")

    # We need to import the module *after* patching the environment
    # because Settings() is instantiated at module import time
    from src.config import Settings
    settings = Settings()

    # Assertions: Verify that the settings object contains the expected values
    assert settings.azure_openai_api_key == "fake_key_for_testing"
    assert settings.azure_openai_endpoint == "https://fake.endpoint.com/"
    assert settings.openai_api_version == "2023-12-01-preview"

    # Test default values
    assert settings.embedding_model_name == "text-embedding-ada-002"
    assert settings.llm_model_name == "gpt-4o"


def test_settings_missing_api_key_raises_error(monkeypatch):
    """
    Tests that a ValueError is raised if AZURE_OPENAI_API_KEY is missing.

    This verifies the "fail fast" behavior - the application should not start
    if required configuration is missing.
    """
    # Ensure the API key is NOT set
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)

    # Set the other required variables
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://fake.endpoint.com/")
    monkeypatch.setenv("OPENAI_API_VERSION", "2023-12-01-preview")

    from src.config import Settings

    # Use pytest.raises to assert that a specific exception is thrown
    with pytest.raises(ValueError, match="Error: Environment variable 'AZURE_OPENAI_API_KEY' not set"):
        Settings()


def test_settings_missing_endpoint_raises_error(monkeypatch):
    """
    Tests that a ValueError is raised if AZURE_OPENAI_ENDPOINT is missing.
    """
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "fake_key")
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.setenv("OPENAI_API_VERSION", "2023-12-01-preview")

    from src.config import Settings

    with pytest.raises(ValueError, match="Error: Environment variable 'AZURE_OPENAI_ENDPOINT' not set"):
        Settings()


def test_settings_missing_api_version_raises_error(monkeypatch):
    """
    Tests that a ValueError is raised if OPENAI_API_VERSION is missing.
    """
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "fake_key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://fake.endpoint.com/")
    monkeypatch.delenv("OPENAI_API_VERSION", raising=False)

    from src.config import Settings

    with pytest.raises(ValueError, match="Error: Environment variable 'OPENAI_API_VERSION' not set"):
        Settings()


def test_settings_custom_model_names(monkeypatch):
    """
    Tests that custom model names can be set via environment variables.
    """
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "fake_key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://fake.endpoint.com/")
    monkeypatch.setenv("OPENAI_API_VERSION", "2023-12-01-preview")
    monkeypatch.setenv("EMBEDDING_MODEL_NAME", "custom-embedding-model")
    monkeypatch.setenv("LLM_MODEL_NAME", "custom-llm-model")

    from src.config import Settings
    settings = Settings()

    assert settings.embedding_model_name == "custom-embedding-model"
    assert settings.llm_model_name == "custom-llm-model"
