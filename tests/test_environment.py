"""
Tests for v2.0 environment setup and configuration.

Ensures all required dependencies and configurations are available.
"""

import pytest
import sys
import importlib
from pathlib import Path


class TestDependencies:
    """Test that all required dependencies are installed."""
    
    def test_langgraph_available(self):
        """Test LangGraph is installed and importable."""
        try:
            import langgraph
            assert hasattr(langgraph, '__version__')
        except ImportError:
            pytest.fail("LangGraph not installed")
    
    def test_langgraph_version(self):
        """Test LangGraph version is 0.0.20 or higher."""
        import langgraph
        from packaging import version
        assert version.parse(langgraph.__version__) >= version.parse("0.0.20")
    
    def test_langchain_available(self):
        """Test LangChain is installed."""
        try:
            import langchain
            assert hasattr(langchain, '__version__')
        except ImportError:
            pytest.fail("LangChain not installed")
    
    def test_langchain_openai_available(self):
        """Test langchain-openai is installed."""
        try:
            from langchain_openai import AzureChatOpenAI
        except ImportError:
            pytest.fail("langchain-openai not installed")
    
    def test_gitpython_available(self):
        """Test gitpython is installed."""
        try:
            import git
        except ImportError:
            pytest.fail("gitpython not installed")
    
    def test_libcst_available(self):
        """Test libcst is installed."""
        try:
            import libcst
        except ImportError:
            pytest.fail("libcst not installed")
    
    def test_all_v1_dependencies(self):
        """Test all v1.0 dependencies still available."""
        required = [
            'chromadb',
            'openai',
            'dotenv',
            'pdf2image',
            'PIL',
            'pytest'
        ]
        
        for module_name in required:
            try:
                if module_name == 'dotenv':
                    import dotenv
                elif module_name == 'PIL':
                    from PIL import Image
                else:
                    importlib.import_module(module_name)
            except ImportError:
                pytest.fail(f"v1.0 dependency missing: {module_name}")


class TestEnvironmentVariables:
    """Test environment variable configuration."""
    
    def test_env_example_exists(self):
        """Test .env.example file exists."""
        env_example = Path(".env.example")
        assert env_example.exists(), ".env.example not found"
    
    def test_env_example_has_v2_variables(self):
        """Test .env.example contains v2.0 variables."""
        env_example = Path(".env.example")
        content = env_example.read_text()
        
        required_vars = [
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "OPENAI_API_VERSION",
            "EMBEDDING_MODEL_NAME",
            "LLM_MODEL_NAME",
            "AGENT_MAX_ITERATIONS",
            "AGENT_REFLECTION_ENABLED"
        ]
        
        for var in required_vars:
            assert var in content, f"Missing env var in .env.example: {var}"
    
    def test_langsmith_variables_optional(self):
        """Test LangSmith variables are documented as optional."""
        env_example = Path(".env.example")
        content = env_example.read_text()
        
        # Should have LangSmith vars with (optional) note
        assert "LANGSMITH" in content
        assert "optional" in content.lower() or "Optional" in content


class TestProjectStructure:
    """Test project directory structure."""
    
    def test_src_directory_exists(self):
        """Test src/ directory exists."""
        assert Path("src").exists()
        assert Path("src").is_dir()
    
    def test_tests_directory_exists(self):
        """Test tests/ directory exists."""
        assert Path("tests").exists()
        assert Path("tests").is_dir()
    
    def test_docs_v2_directory_exists(self):
        """Test docs/v2.0/ directory exists."""
        assert Path("docs/v2.0").exists()
        assert Path("docs/v2.0").is_dir()


class TestBackwardCompatibility:
    """Test that v1.0 functionality is not broken."""
    
    def test_v1_config_imports(self):
        """Test v1.0 config still imports."""
        try:
            from src.config import Settings
            # Don't instantiate as it requires env vars - just check import works
            assert Settings is not None
        except Exception as e:
            pytest.fail(f"v1.0 Settings import failed: {e}")
    
    def test_v1_modules_importable(self):
        """Test all v1.0 modules can be imported."""
        modules = [
            'src.config',
            'src.data_loader',
            'src.text_processor',
            'src.vector_store',
            'src.chatbot'
        ]
        
        for module in modules:
            try:
                importlib.import_module(module)
            except Exception as e:
                pytest.fail(f"Cannot import {module}: {e}")


def test_python_version():
    """Test Python version is 3.11 or higher."""
    assert sys.version_info >= (3, 11), "Python 3.11+ required"


def test_requirements_file_exists():
    """Test requirements.txt exists and is readable."""
    req_file = Path("requirements.txt")
    assert req_file.exists(), "requirements.txt not found"
    
    content = req_file.read_text()
    assert len(content) > 0, "requirements.txt is empty"
