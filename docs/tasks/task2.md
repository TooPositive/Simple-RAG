Excellent. Here is the next task, focusing on securely managing the configuration and API keys needed for the project.

-----

### **Spec Task `SETUP-2`: Secure Configuration Loader**

#### **🎯 Objective**

To implement a robust mechanism for loading sensitive information (like API keys and endpoints) from the environment, ensuring that no secrets are hardcoded in the source code. This promotes security and makes the application easily configurable for different environments (development, production).

#### **🔑 Key Components & Rationale**

  * **`.env` file:** A standard file for storing environment variables locally during development. It is **never** committed to version control.
  * **`.env.example` file:** A template file that *is* committed to version control. It shows other developers what variables are required to run the application.
  * **`python-dotenv` library:** The library used to automatically load the key-value pairs from the `.env` file into the application's environment when it starts.
  * **Configuration Module (`src/config.py`):** A centralized Python module responsible for reading the environment variables and making them available to the rest of the application. This module will also perform validation, raising an error if a required variable is not set.

#### **✅ Acceptance Criteria**

1.  A file named `src/config.py` is created.
2.  It contains a class or object that loads required Azure OpenAI credentials (`API_KEY`, `ENDPOINT`, `API_VERSION`).
3.  The application will raise a `ValueError` on startup if any of these required variables are missing.
4.  A file named `.env.example` exists in the root directory to serve as a template.
5.  A unit test file `tests/test_config.py` is created.
6.  The test successfully verifies that the configuration is loaded correctly from a *temporary, fake* `.env` file.
7.  The test also verifies that a `ValueError` is raised when a required variable is omitted.

#### **📝 Detailed Steps**

1.  **Create the Configuration Module:**
    Create the file `src/config.py` and add the following Python code. This class will read from the environment and fail fast if anything is missing.

    ```python
    # src/config.py
    import os
    from dotenv import load_dotenv

    # Load environment variables from a .env file
    load_dotenv()

    class Settings:
        """
        Loads and validates application settings from environment variables.
        """
        def __init__(self):
            # Azure OpenAI API settings
            self.azure_openai_api_key = self._get_env_variable("AZURE_OPENAI_API_KEY")
            self.azure_openai_endpoint = self._get_env_variable("AZURE_OPENAI_ENDPOINT")
            self.openai_api_version = self._get_env_variable("OPENAI_API_VERSION")
            self.embedding_model_name = "text-embedding-ada-002" # Or your preferred model
            self.llm_model_name = "gpt-4" # Or your preferred model

        def _get_env_variable(self, var_name: str) -> str:
            """
            Retrieves an environment variable or raises an error if it's not found.
            """
            value = os.getenv(var_name)
            if value is None:
                raise ValueError(f"Error: Environment variable '{var_name}' not set.")
            return value

    # Create a singleton instance to be imported by other modules
    settings = Settings()
    ```

2.  **Create the Environment File Template:**
    In the root directory of your project, create a file named `.env.example` with the following content. Remember to fill out your *actual* `.env` file but **do not commit it**.

    ```
    # Azure OpenAI Credentials - DO NOT COMMIT THE .env FILE
    AZURE_OPENAI_API_KEY="your_api_key_here"
    AZURE_OPENAI_ENDPOINT="https://your_endpoint.openai.azure.com/"
    OPENAI_API_VERSION="2023-07-01-preview" # Use a specific, valid API version
    ```

3.  **Implement the Unit Test (TDD):**
    Create the file `tests/test_config.py`. This test will ensure your config loader works as expected without needing a real `.env` file present during testing.

    ```python
    # tests/test_config.py
    import pytest
    import os

    def test_settings_load_successfully(monkeypatch):
        """
        Tests that settings are loaded correctly when all env vars are present.
        """
        # Use monkeypatch to set environment variables for the duration of this test
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "fake_key")
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "fake_endpoint")
        monkeypatch.setenv("OPENAI_API_VERSION", "fake_version")

        # We need to import the module *after* patching the environment
        from src.config import Settings
        settings = Settings()

        assert settings.azure_openai_api_key == "fake_key"
        assert settings.azure_openai_endpoint == "fake_endpoint"
        assert settings.openai_api_version == "fake_version"

    def test_settings_missing_variable_raises_error(monkeypatch):
        """
        Tests that a ValueError is raised if a required env var is missing.
        """
        # Ensure the environment is clean for this test
        monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "fake_endpoint")
        monkeypatch.setenv("OPENAI_API_VERSION", "fake_version")

        from src.config import Settings
        
        # Use pytest.raises to assert that a specific exception is thrown
        with pytest.raises(ValueError, match="Error: Environment variable 'AZURE_OPENAI_API_KEY' not set."):
            Settings()

    ```

#### **🧪 TDD - Verification**

1.  Make sure you are in the root `rag-chatbot` directory with your virtual environment active.
2.  Run the tests using `pytest`:
    ```bash
    pytest
    ```
3.  The output should show that both tests in `tests/test_config.py` passed. This confirms your configuration loader is working correctly and is resilient to missing environment variables.