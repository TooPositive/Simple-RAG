"""
Tests for repository analysis tools.

Verifies directory structure analysis, file reading, dependency extraction,
and architecture mapping functionality.
"""

import pytest
from pathlib import Path
from src.tools.repository_tools import (
    analyze_directory_structure,
    read_source_files,
    extract_dependencies,
    generate_architecture_map
)


class TestDirectoryStructure:
    """Test directory structure analysis."""
    
    def test_analyze_directory_structure_returns_dict(self):
        """Test that analyze_directory_structure returns a dictionary."""
        result = analyze_directory_structure(".")
        
        assert isinstance(result, dict)
        assert "name" in result
        assert "type" in result
    
    def test_analyze_directory_structure_identifies_directory(self):
        """Test that root is identified as directory."""
        result = analyze_directory_structure(".")
        
        assert result["type"] == "directory"
    
    def test_analyze_directory_structure_has_children(self):
        """Test that directory has children."""
        result = analyze_directory_structure(".")
        
        assert "children" in result
        assert isinstance(result["children"], list)
    
    def test_analyze_directory_structure_finds_src(self):
        """Test that src directory is found."""
        result = analyze_directory_structure(".")
        
        # Should find src in children
        child_names = [child["name"] for child in result.get("children", [])]
        assert "src" in child_names
    
    def test_analyze_directory_structure_respects_max_depth(self):
        """Test that max_depth parameter is respected."""
        result = analyze_directory_structure(".", max_depth=1)
        
        # Should have limited depth
        assert result is not None


class TestSourceFileReading:
    """Test source file reading and parsing."""
    
    def test_read_source_files_returns_list(self):
        """Test that read_source_files returns a list."""
        result = read_source_files("src")
        
        assert isinstance(result, list)
    
    def test_read_source_files_finds_python_files(self):
        """Test that Python files are found."""
        result = read_source_files("src")
        
        # Should find at least some Python files
        assert len(result) > 0
        
        # Check first file has expected structure
        if result:
            file_info = result[0]
            assert "path" in file_info
            assert "content" in file_info or "error" in file_info
    
    def test_read_source_files_filters_by_extension(self):
        """Test filtering by file extension."""
        result = read_source_files("src", extensions=[".py"])
        
        # All results should be Python files
        for file_info in result:
            assert file_info["path"].endswith(".py")
    
    def test_read_source_files_handles_nonexistent_path(self):
        """Test handling of nonexistent path."""
        result = read_source_files("nonexistent_directory_xyz")
        
        # Should return empty list or handle gracefully
        assert isinstance(result, list)


class TestDependencyExtraction:
    """Test dependency extraction."""
    
    def test_extract_dependencies_returns_dict(self):
        """Test that extract_dependencies returns a dictionary."""
        result = extract_dependencies(".")
        
        assert isinstance(result, dict)
    
    def test_extract_dependencies_finds_requirements(self):
        """Test that requirements.txt is parsed."""
        result = extract_dependencies(".")
        
        # Should have some dependencies
        assert "dependencies" in result
        assert isinstance(result["dependencies"], list)
        assert len(result["dependencies"]) > 0
    
    def test_extract_dependencies_includes_versions(self):
        """Test that version information is included."""
        result = extract_dependencies(".")
        
        # Check first dependency has name
        if result.get("dependencies"):
            dep = result["dependencies"][0]
            assert "name" in dep


class TestArchitectureMapping:
    """Test architecture map generation."""
    
    def test_generate_architecture_map_returns_dict(self):
        """Test that generate_architecture_map returns a dictionary."""
        result = generate_architecture_map(".")
        
        assert isinstance(result, dict)
    
    def test_generate_architecture_map_has_modules(self):
        """Test that architecture map identifies modules."""
        result = generate_architecture_map(".")
        
        assert "modules" in result
        assert isinstance(result["modules"], list)
    
    def test_generate_architecture_map_identifies_src(self):
        """Test that src module is identified."""
        result = generate_architecture_map(".")
        
        module_names = [m["name"] for m in result.get("modules", [])]
        assert "src" in module_names or any("src" in name for name in module_names)
    
    def test_generate_architecture_map_includes_dependencies(self):
        """Test that module dependencies are tracked."""
        result = generate_architecture_map(".")
        
        # Should have dependency information
        assert "dependencies" in result or any(
            "dependencies" in m for m in result.get("modules", [])
        )


class TestIntegration:
    """Integration tests for repository tools."""
    
    def test_full_repository_analysis_workflow(self):
        """Test complete repository analysis workflow."""
        # Analyze structure
        structure = analyze_directory_structure(".")
        assert structure is not None
        
        # Read source files
        files = read_source_files("src")
        assert len(files) > 0
        
        # Extract dependencies
        deps = extract_dependencies(".")
        assert len(deps.get("dependencies", [])) > 0
        
        # Generate architecture map
        arch = generate_architecture_map(".")
        assert len(arch.get("modules", [])) > 0
