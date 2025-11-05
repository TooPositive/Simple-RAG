"""
Repository analyzer node.

This node analyzes the codebase using repository tools.
"""

import os
from src.agent.state import AgentState
from src.tools.repository_tools import (
    analyze_directory_structure,
    read_source_files,
    extract_dependencies,
    generate_architecture_map,
    extract_code_symbols
)
from src.utils.cache import get_cache


async def repo_analyzer_node(state: AgentState) -> AgentState:
    """
    Analyze repository structure and code.
    
    Uses repository analysis tools to understand the codebase structure,
    dependencies, and architecture.
    
    Args:
        state: Current agent state
    
    Returns:
        AgentState: Updated state with repository analysis
    """
    new_state = dict(state)
    
    # Find the repository root (where this script is running)
    # Assume we're in Simple-RAG/ directory
    repo_root = os.getcwd()
    if "Simple-RAG" not in repo_root:
        # Try to find it
        for parent in ["..", "../..", "../../.."]:
            test_path = os.path.join(parent, "Simple-RAG")
            if os.path.exists(test_path):
                repo_root = os.path.abspath(test_path)
                break
    
    # Check session cache first (from previous query in same session)
    has_session_cache = bool(state.get("code_symbols") and state.get("verification_outputs"))

    if has_session_cache:
        print(f"📦 Using fully cached repository analysis (skipping expensive operations)")
        # Keep existing cached data
        print(f"  ✓ Repo structure: {len(state.get('repo_structure', {}).get('children', []))} items (cached)")
        print(f"  ✓ Code files: {len(state.get('code_files', []))} files (cached)")
        print(f"  ✓ Dependencies: {state.get('dependencies', {}).get('count', 0)} (cached)")
        print(f"  ✓ Architecture: {len(state.get('architecture', {}).get('modules', []))} modules (cached)")
        symbols = state.get("code_symbols", {})
        print(f"  ✓ Code symbols: {symbols.get('summary', {}).get('total_classes', 0)} classes, {symbols.get('summary', {}).get('total_functions', 0)} functions (cached)")
        verif = state.get("verification_outputs", {})
        if "pytest_collect" in verif:
            print(f"  ✓ Pytest collection (cached)")
        if "coverage_report" in verif:
            print(f"  ✓ Coverage report (cached)")
        # Keep all cached data in new_state
        return new_state

    # Check persistent disk cache (survives sessions)
    cache = get_cache()
    cached_data = cache.get(repo_root)

    if cached_data:
        # Load from disk cache
        new_state["repo_structure"] = cached_data.get("repo_structure")
        new_state["code_files"] = cached_data.get("code_files")
        new_state["dependencies"] = cached_data.get("dependencies")
        new_state["architecture"] = cached_data.get("architecture")
        new_state["code_symbols"] = cached_data.get("code_symbols")
        new_state["verification_outputs"] = cached_data.get("verification_outputs")

        # Show cache summary
        symbols = new_state.get("code_symbols", {})
        print(f"  ✓ Code symbols: {symbols.get('summary', {}).get('total_classes', 0)} classes, {symbols.get('summary', {}).get('total_functions', 0)} functions (cached)")

        # Next: Go to reasoner
        new_state["next_action"] = "generate"

        return new_state

    print(f"🔍 Analyzing repository at: {repo_root}")
    
    # Analyze directory structure
    structure = analyze_directory_structure(repo_root, max_depth=3)
    new_state["repo_structure"] = structure
    children_count = len(structure.get('children', []))
    print(f"  ✓ Found {children_count} top-level items")
    
    # Read source files (limited to avoid overwhelming)
    src_path = os.path.join(repo_root, "src")
    files = read_source_files(src_path, max_files=20)
    new_state["code_files"] = files
    print(f"  ✓ Analyzed {len(files)} source files")
    
    # Extract dependencies
    deps = extract_dependencies(repo_root)
    new_state["dependencies"] = deps
    deps_count = deps.get('count', len(deps.get('dependencies', [])))
    print(f"  ✓ Identified {deps_count} dependencies")
    
    # Generate architecture map
    arch = generate_architecture_map(repo_root)
    new_state["architecture"] = arch
    modules_count = arch.get('total_modules', len(arch.get('modules', [])))
    print(f"  ✓ Mapped {modules_count} modules")
    
    # 🔥 CRITICAL: Extract actual code symbols (classes, functions, tests)
    # This is what makes the analysis EVIDENCE-BASED!
    symbols = extract_code_symbols(repo_root, max_files=50)
    new_state["code_symbols"] = symbols
    symbols_count = symbols["summary"]["total_classes"] + symbols["summary"]["total_functions"]
    print(f"  ✓ Extracted {symbols_count} code symbols ({symbols['summary']['total_classes']} classes, {symbols['summary']['total_functions']} functions)")
    print(f"    Note: {symbols['summary']['total_tests']} test functions found via AST (pytest will find more including parametrized tests)")
    
    # 🔥 RUN ACTUAL VERIFICATION COMMANDS (CEO requirement)
    import subprocess
    verification_outputs = {}
    
    try:
        # Count actual tests with pytest (increased timeout for large test suites)
        result = subprocess.run(
            ["pytest", "--collect-only", "-q"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=60  # Increased from 10s to 60s for larger projects
        )
        verification_outputs["pytest_collect"] = result.stdout + result.stderr
        print(f"  ✓ Ran pytest --collect-only")
    except Exception as e:
        verification_outputs["pytest_collect"] = f"ERROR: {str(e)}"
    
    # Check if coverage should be skipped
    skip_coverage = os.getenv("SKIP_COVERAGE", "false").lower() == "true"
    
    if skip_coverage:
        verification_outputs["coverage_report"] = "Coverage skipped (SKIP_COVERAGE=true)"
        print(f"  ⏭️  Coverage skipped (set SKIP_COVERAGE=false to enable)")
    else:
        try:
            # Check if .coverage file already exists (cached)
            coverage_file = os.path.join(repo_root, ".coverage")
            if os.path.exists(coverage_file):
                # Use cached coverage
                print(f"  📦 Using cached coverage data...")
                result = subprocess.run(
                    ["coverage", "report"],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    verification_outputs["coverage_report"] = result.stdout
                    import re
                    match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', result.stdout)
                    if match:
                        coverage_pct = match.group(1)
                        print(f"  ✓ Coverage: {coverage_pct}% (cached)")
                    else:
                        print(f"  ✓ Coverage report (cached)")
                else:
                    # Cache is stale, need to re-run
                    raise Exception("Cached coverage stale")
            else:
                # No cache, check if coverage is available
                check_result = subprocess.run(
                    ["which", "coverage"],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if check_result.returncode == 0:
                    # Coverage is installed, run tests with coverage
                    print(f"  ⏳ Running tests with coverage (this may take 30 seconds)...")
                    run_result = subprocess.run(
                        ["coverage", "run", "-m", "pytest", "-q", "--tb=no"],
                        cwd=repo_root,
                        capture_output=True,
                        text=True,
                        timeout=30  # Reduced from 60 to 30
                    )
                    
                    # Get the coverage report
                    report_result = subprocess.run(
                        ["coverage", "report"],
                        cwd=repo_root,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if report_result.returncode == 0:
                        verification_outputs["coverage_report"] = report_result.stdout
                        verification_outputs["coverage_run_output"] = run_result.stdout + run_result.stderr
                        
                        # Extract summary stats
                        import re
                        match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', report_result.stdout)
                        if match:
                            coverage_pct = match.group(1)
                            print(f"  ✓ Coverage: {coverage_pct}%")
                        else:
                            print(f"  ✓ Coverage report generated")
                    else:
                        verification_outputs["coverage_report"] = f"Coverage report failed: {report_result.stderr}"
                        print(f"  ⚠️  Coverage report failed")
                else:
                    verification_outputs["coverage_report"] = "Coverage tool not installed"
                    print(f"  ℹ️  Coverage not installed (pip install coverage)")
        except subprocess.TimeoutExpired:
            verification_outputs["coverage_report"] = "Coverage timed out - skipping (set SKIP_COVERAGE=true to disable)"
            print(f"  ⚠️  Coverage timed out (taking >30s) - set SKIP_COVERAGE=true to disable")
        except Exception as e:
            verification_outputs["coverage_report"] = f"Coverage skipped: {str(e)}"
            print(f"  ℹ️  Coverage skipped: {str(e)}")
    
    try:
        # Count test files
        result = subprocess.run(
            ["find", "tests", "-name", "*.py", "-type", "f"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5
        )
        test_files = result.stdout.strip().split("\n") if result.stdout.strip() else []
        verification_outputs["test_files_count"] = len([f for f in test_files if f])
        print(f"  ✓ Counted {verification_outputs['test_files_count']} test files")
    except Exception:
        verification_outputs["test_files_count"] = "Unknown"
    
    new_state["verification_outputs"] = verification_outputs
    
    # Add reasoning steps
    new_state["reasoning_steps"] = state["reasoning_steps"] + [
        f"Repository analysis: Found {children_count} top-level items",
        f"Repository analysis: Analyzed {len(files)} source files",
        f"Repository analysis: Identified {deps_count} dependencies",
        f"Repository analysis: Mapped {modules_count} modules",
        f"Repository analysis: Extracted {symbols_count} code symbols for evidence-based analysis"
    ]
    
    # Log tool usage
    new_state["tool_usage"] = state["tool_usage"] + [{
        "tool": "repository_analysis",
        "files_analyzed": len(files),
        "dependencies_found": deps_count,
        "modules_found": modules_count
    }]

    # Save to persistent cache for future sessions
    cache_data = {
        "repo_structure": new_state["repo_structure"],
        "code_files": new_state["code_files"],
        "dependencies": new_state["dependencies"],
        "architecture": new_state["architecture"],
        "code_symbols": new_state["code_symbols"],
        "verification_outputs": new_state["verification_outputs"]
    }
    cache.set(repo_root, cache_data)

    return new_state
