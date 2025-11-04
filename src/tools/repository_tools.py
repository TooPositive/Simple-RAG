"""
Repository analysis tools.

Provides tools for the agent to analyze its own codebase:
    - Directory structure analysis
    - Source file reading and parsing
    - Dependency extraction
    - Architecture mapping
    - Code symbol extraction (classes, functions, tests)
"""

import os
import ast
from pathlib import Path
from typing import Dict, List, Optional
import re


def analyze_directory_structure(
    root_path: str,
    max_depth: int = 5,
    ignore_patterns: Optional[List[str]] = None
) -> Dict:
    """
    Analyze repository directory structure.
    
    Recursively analyzes the directory tree, respecting gitignore patterns
    and depth limits.
    
    Args:
        root_path: Root directory to analyze
        max_depth: Maximum depth to traverse (default: 5)
        ignore_patterns: Patterns to ignore (default: common patterns)
    
    Returns:
        Dict: Directory structure with name, type, and children
    
    Example:
        >>> structure = analyze_directory_structure(".")
        >>> structure["type"]
        'directory'
    """
    if ignore_patterns is None:
        ignore_patterns = [
            "__pycache__", ".git", ".venv", "node_modules",
            ".pytest_cache", ".mypy_cache", "*.pyc", ".DS_Store"
        ]
    
    def should_ignore(name: str) -> bool:
        """Check if path should be ignored."""
        for pattern in ignore_patterns:
            if pattern.startswith("*"):
                if name.endswith(pattern[1:]):
                    return True
            elif name == pattern or pattern in name:
                return True
        return False
    
    def analyze_path(path: Path, depth: int) -> Dict:
        """Recursively analyze a path."""
        if depth > max_depth:
            return None
        
        name = path.name
        
        if should_ignore(name):
            return None
        
        if path.is_file():
            return {
                "name": name,
                "type": "file",
                "size": path.stat().st_size if path.exists() else 0
            }
        elif path.is_dir():
            children = []
            try:
                for child_path in sorted(path.iterdir()):
                    child_info = analyze_path(child_path, depth + 1)
                    if child_info:
                        children.append(child_info)
            except PermissionError:
                pass
            
            return {
                "name": name,
                "type": "directory",
                "children": children
            }
        
        return None
    
    root = Path(root_path)
    return analyze_path(root, 0) or {"name": root.name, "type": "directory", "children": []}


def read_source_files(
    root_path: str,
    extensions: Optional[List[str]] = None,
    max_files: int = 100
) -> List[Dict]:
    """
    Read and parse source code files.
    
    Reads source files from the repository, extracting content and
    basic metadata.
    
    Args:
        root_path: Root directory to search
        extensions: File extensions to include (default: [".py"])
        max_files: Maximum number of files to read (default: 100)
    
    Returns:
        List[Dict]: List of file information dictionaries
    
    Example:
        >>> files = read_source_files("src")
        >>> files[0]["path"]
        'src/config.py'
    """
    if extensions is None:
        extensions = [".py"]
    
    files = []
    root = Path(root_path)
    
    if not root.exists():
        return []
    
    # Find all matching files
    for ext in extensions:
        for file_path in root.rglob(f"*{ext}"):
            if len(files) >= max_files:
                break
            
            # Skip ignored directories
            if any(part.startswith(".") or part == "__pycache__" 
                   for part in file_path.parts):
                continue
            
            try:
                content = file_path.read_text(encoding="utf-8")
                files.append({
                    "path": str(file_path),
                    "name": file_path.name,
                    "content": content,
                    "lines": len(content.splitlines()),
                    "size": len(content)
                })
            except Exception as e:
                files.append({
                    "path": str(file_path),
                    "name": file_path.name,
                    "error": str(e)
                })
    
    return files


def extract_dependencies(root_path: str) -> Dict:
    """
    Extract project dependencies.
    
    Parses requirements.txt and other dependency files to extract
    project dependencies.
    
    Args:
        root_path: Root directory to search
    
    Returns:
        Dict: Dependencies information
    
    Example:
        >>> deps = extract_dependencies(".")
        >>> len(deps["dependencies"]) > 0
        True
    """
    root = Path(root_path)
    dependencies = []
    
    # Try to find requirements.txt
    req_file = root / "requirements.txt"
    if req_file.exists():
        try:
            content = req_file.read_text()
            for line in content.splitlines():
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                
                # Parse dependency
                # Handle formats: package==version, package>=version, package
                match = re.match(r"^([a-zA-Z0-9_-]+)([><=!]+)?(.+)?", line)
                if match:
                    name = match.group(1)
                    operator = match.group(2) or ""
                    version = match.group(3) or ""
                    
                    dependencies.append({
                        "name": name,
                        "version": version.strip() if version else None,
                        "operator": operator,
                        "raw": line
                    })
        except Exception as e:
            pass
    
    return {
        "dependencies": dependencies,
        "source": "requirements.txt" if req_file.exists() else "none",
        "count": len(dependencies)
    }


def generate_architecture_map(root_path: str) -> Dict:
    """
    Generate architecture understanding.
    
    Analyzes the codebase structure to understand the architecture,
    identifying modules, their relationships, and key components.
    
    Args:
        root_path: Root directory to analyze
    
    Returns:
        Dict: Architecture map with modules and dependencies
    
    Example:
        >>> arch = generate_architecture_map(".")
        >>> "modules" in arch
        True
    """
    root = Path(root_path)
    modules = []
    
    # Find Python packages (directories with __init__.py)
    for init_file in root.rglob("__init__.py"):
        module_dir = init_file.parent
        
        # Skip hidden and cache directories
        if any(part.startswith(".") or part == "__pycache__" 
               for part in module_dir.parts):
            continue
        
        # Get module name
        try:
            rel_path = module_dir.relative_to(root)
            module_name = str(rel_path).replace(os.sep, ".")
        except ValueError:
            module_name = module_dir.name
        
        # Count Python files in module
        py_files = list(module_dir.glob("*.py"))
        
        modules.append({
            "name": module_name,
            "path": str(module_dir),
            "files": len(py_files),
            "is_package": True
        })
    
    # Extract high-level dependencies
    deps_info = extract_dependencies(root_path)
    
    return {
        "modules": modules,
        "dependencies": deps_info["dependencies"],
        "total_modules": len(modules),
        "architecture_type": "modular" if len(modules) > 1 else "simple"
    }


def extract_code_symbols(root_path: str, max_files: int = 50) -> Dict:
    """
    Extract actual code symbols (classes, functions, tests) from Python files.
    
    THIS IS THE KEY FUNCTION FOR EVIDENCE-BASED ANALYSIS!
    Parses Python files using AST to extract real class names, function names,
    and test names that can be cited in analysis.
    
    Args:
        root_path: Root directory to search
        max_files: Maximum number of files to parse (default: 50)
    
    Returns:
        Dict: Code symbols organized by file with classes, functions, and tests
    
    Example:
        >>> symbols = extract_code_symbols("src")
        >>> symbols["files"][0]["classes"]
        ['AgentRunner', 'PlanningNode']
    """
    root = Path(root_path)
    files_with_symbols = []
    all_classes = []
    all_functions = []
    all_tests = []
    
    # Find Python files
    py_files = []
    for py_file in root.rglob("*.py"):
        # Skip ignored directories
        if any(part.startswith(".") or part == "__pycache__" 
               for part in py_file.parts):
            continue
        py_files.append(py_file)
        
        if len(py_files) >= max_files:
            break
    
    for file_path in py_files:
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))
            
            classes = []
            functions = []
            tests = []
            
            for node in ast.walk(tree):
                # Extract class names
                if isinstance(node, ast.ClassDef):
                    class_name = node.name
                    classes.append(class_name)
                    all_classes.append({
                        "name": class_name,
                        "file": str(file_path.relative_to(root)),
                        "line": node.lineno
                    })
                
                # Extract function names (top-level and methods)
                elif isinstance(node, ast.FunctionDef):
                    func_name = node.name
                    functions.append(func_name)
                    
                    # Check if it's a test function
                    is_test = func_name.startswith("test_") or "test" in str(file_path).lower()
                    
                    if is_test:
                        tests.append(func_name)
                        all_tests.append({
                            "name": func_name,
                            "file": str(file_path.relative_to(root)),
                            "line": node.lineno
                        })
                    else:
                        all_functions.append({
                            "name": func_name,
                            "file": str(file_path.relative_to(root)),
                            "line": node.lineno
                        })
            
            # Only add files that have symbols
            if classes or functions or tests:
                files_with_symbols.append({
                    "file": str(file_path.relative_to(root)),
                    "classes": classes,
                    "functions": functions,
                    "tests": tests,
                    "total_symbols": len(classes) + len(functions) + len(tests)
                })
        
        except (SyntaxError, UnicodeDecodeError) as e:
            # Skip files with syntax errors or encoding issues
            continue
    
    return {
        "files": files_with_symbols,
        "all_classes": all_classes,
        "all_functions": all_functions,
        "all_tests": all_tests,
        "summary": {
            "total_files": len(files_with_symbols),
            "total_classes": len(all_classes),
            "total_functions": len(all_functions),
            "total_tests": len(all_tests)
        }
    }
