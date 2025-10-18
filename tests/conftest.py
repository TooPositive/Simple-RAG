# tests/conftest.py
"""
Pytest configuration file.

This file contains fixtures and configuration that apply to all tests.
Most importantly, it sets up mock environment variables AT MODULE IMPORT TIME
before any test modules are imported, preventing the Settings singleton from
failing during test imports.

For real integration tests (marked with @pytest.mark.real_integration),
the actual .env values are preserved and used instead of test values.
"""

import pytest
import os
from dotenv import load_dotenv

# Load .env file first if it exists
load_dotenv()

# CRITICAL: Set environment variables at module level BEFORE any imports
# This ensures that when test modules import src.config, the settings
# singleton can be instantiated successfully.
#
# Only set test values if the environment variables are not already set
# (i.e., not loaded from .env). This allows real integration tests to use
# actual Azure credentials.
if "AZURE_OPENAI_API_KEY" not in os.environ:
    os.environ["AZURE_OPENAI_API_KEY"] = "test_key"
if "AZURE_OPENAI_ENDPOINT" not in os.environ:
    os.environ["AZURE_OPENAI_ENDPOINT"] = "https://test.endpoint.com/"
if "OPENAI_API_VERSION" not in os.environ:
    os.environ["OPENAI_API_VERSION"] = "2023-12-01-preview"
if "EMBEDDING_MODEL_NAME" not in os.environ:
    os.environ["EMBEDDING_MODEL_NAME"] = "text-embedding-ada-002"
if "LLM_MODEL_NAME" not in os.environ:
    os.environ["LLM_MODEL_NAME"] = "gpt-4o"

# Register the real_integration mark to suppress warnings
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "real_integration: mark test as a real integration test (makes real API calls, costs money)"
    )
