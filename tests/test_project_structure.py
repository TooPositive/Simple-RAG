"""
Tests for v2.0 project structure verification.

Ensures all required directories and files exist for the v2.0 agentic system.
"""

import pytest
from pathlib import Path
import importlib


class TestDirectoryStructure:
    """Test that all required directories exist."""
    
    def test_agent_directory_exists(self):
        """Test src/agent/ directory exists."""
        agent_dir = Path("src/agent")
        assert agent_dir.exists(), "src/agent/ not found"
        assert agent_dir.is_dir(), "src/agent/ is not a directory"
    
    def test_agent_nodes_directory_exists(self):
        """Test src/agent/nodes/ directory exists."""
        nodes_dir = Path("src/agent/nodes")
        assert nodes_dir.exists(), "src/agent/nodes/ not found"
        assert nodes_dir.is_dir(), "src/agent/nodes/ is not a directory"
    
    def test_tools_directory_exists(self):
        """Test src/tools/ directory exists."""
        tools_dir = Path("src/tools")
        assert tools_dir.exists(), "src/tools/ not found"
        assert tools_dir.is_dir(), "src/tools/ is not a directory"
    
    def test_evaluation_directory_exists(self):
        """Test src/evaluation/ directory exists."""
        eval_dir = Path("src/evaluation")
        assert eval_dir.exists(), "src/evaluation/ not found"
        assert eval_dir.is_dir(), "src/evaluation/ is not a directory"
    
    def test_tests_structure_mirrors_src(self):
        """Test test directories mirror src structure."""
        test_dirs = [
            Path("tests/test_agent"),
            Path("tests/test_agent/test_nodes"),
            Path("tests/test_tools"),
            Path("tests/test_evaluation")
        ]
        
        for test_dir in test_dirs:
            assert test_dir.exists(), f"{test_dir} not found"
            assert test_dir.is_dir(), f"{test_dir} is not a directory"


class TestInitFiles:
    """Test that all __init__.py files exist."""
    
    def test_agent_init_exists(self):
        """Test src/agent/__init__.py exists."""
        init_file = Path("src/agent/__init__.py")
        assert init_file.exists(), "src/agent/__init__.py not found"
    
    def test_agent_nodes_init_exists(self):
        """Test src/agent/nodes/__init__.py exists."""
        init_file = Path("src/agent/nodes/__init__.py")
        assert init_file.exists(), "src/agent/nodes/__init__.py not found"
    
    def test_tools_init_exists(self):
        """Test src/tools/__init__.py exists."""
        init_file = Path("src/tools/__init__.py")
        assert init_file.exists(), "src/tools/__init__.py not found"
    
    def test_evaluation_init_exists(self):
        """Test src/evaluation/__init__.py exists."""
        init_file = Path("src/evaluation/__init__.py")
        assert init_file.exists(), "src/evaluation/__init__.py not found"
    
    def test_test_agent_init_exists(self):
        """Test tests/test_agent/__init__.py exists."""
        init_file = Path("tests/test_agent/__init__.py")
        assert init_file.exists(), "tests/test_agent/__init__.py not found"


class TestModuleImports:
    """Test that new modules can be imported."""
    
    def test_agent_module_imports(self):
        """Test src.agent module can be imported."""
        try:
            import src.agent
            assert src.agent is not None
        except ImportError as e:
            pytest.fail(f"Cannot import src.agent: {e}")
    
    def test_agent_nodes_module_imports(self):
        """Test src.agent.nodes module can be imported."""
        try:
            import src.agent.nodes
            assert src.agent.nodes is not None
        except ImportError as e:
            pytest.fail(f"Cannot import src.agent.nodes: {e}")
    
    def test_tools_module_imports(self):
        """Test src.tools module can be imported."""
        try:
            import src.tools
            assert src.tools is not None
        except ImportError as e:
            pytest.fail(f"Cannot import src.tools: {e}")
    
    def test_evaluation_module_imports(self):
        """Test src.evaluation module can be imported."""
        try:
            import src.evaluation
            assert src.evaluation is not None
        except ImportError as e:
            pytest.fail(f"Cannot import src.evaluation: {e}")


class TestPlaceholderFiles:
    """Test that placeholder files exist for key components."""
    
    def test_state_placeholder_exists(self):
        """Test src/agent/state.py placeholder exists."""
        state_file = Path("src/agent/state.py")
        assert state_file.exists(), "src/agent/state.py not found"
    
    def test_orchestrator_placeholder_exists(self):
        """Test src/agent/orchestrator.py placeholder exists."""
        orchestrator_file = Path("src/agent/orchestrator.py")
        assert orchestrator_file.exists(), "src/agent/orchestrator.py not found"
    
    def test_repository_tools_placeholder_exists(self):
        """Test src/tools/repository_tools.py placeholder exists."""
        tools_file = Path("src/tools/repository_tools.py")
        assert tools_file.exists(), "src/tools/repository_tools.py not found"
    
    def test_node_placeholders_exist(self):
        """Test all node placeholder files exist."""
        node_files = [
            Path("src/agent/nodes/planner.py"),
            Path("src/agent/nodes/repo_analyzer.py"),
            Path("src/agent/nodes/reasoner.py"),
            Path("src/agent/nodes/reflector.py"),
            Path("src/agent/nodes/generator.py"),
            Path("src/agent/nodes/evaluator.py")
        ]
        
        for node_file in node_files:
            assert node_file.exists(), f"{node_file} not found"


class TestREADMEFiles:
    """Test that README files exist for documentation."""
    
    def test_agent_readme_exists(self):
        """Test src/agent/README.md exists."""
        readme = Path("src/agent/README.md")
        assert readme.exists(), "src/agent/README.md not found"
    
    def test_tools_readme_exists(self):
        """Test src/tools/README.md exists."""
        readme = Path("src/tools/README.md")
        assert readme.exists(), "src/tools/README.md not found"
    
    def test_evaluation_readme_exists(self):
        """Test src/evaluation/README.md exists."""
        readme = Path("src/evaluation/README.md")
        assert readme.exists(), "src/evaluation/README.md not found"


def test_gitignore_updated():
    """Test .gitignore includes new patterns if needed."""
    gitignore = Path(".gitignore")
    assert gitignore.exists(), ".gitignore not found"
    
    content = gitignore.read_text()
    # Should already have Python patterns, but verify
    assert "__pycache__" in content
    assert "*.pyc" in content
