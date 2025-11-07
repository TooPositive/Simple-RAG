"""
Context builder for LLM prompt generation.

This module handles all context construction logic, making it reusable
and testable independently of the main generation logic.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from src.agent.state import AgentState
from src.agent.nodes.config import ContextConfig


class ContextBuilder:
    """
    Builds context strings for LLM prompts from agent state.

    This class encapsulates all context building logic, making it
    easier to test, maintain, and extend.
    """

    def __init__(self, config: Optional[ContextConfig] = None):
        """
        Initialize context builder.

        Args:
            config: Configuration for context building
        """
        self.config = config or ContextConfig()

    def build_context(
        self,
        state: AgentState,
        task: str,
        task_type: str,
        include_reflection: bool = True
    ) -> str:
        """
        Build complete context string from state.

        Args:
            state: Current agent state
            task: User task/query
            task_type: Type of task being performed
            include_reflection: Whether to include reflection notes

        Returns:
            Complete context string for LLM
        """
        context_parts = [f"User Query: {task}\n\n"]

        # Add RAG retrieved context
        retrieved = self._build_rag_context(state)
        if retrieved:
            context_parts.append(retrieved)

        # Add repository analysis data
        repo_context = self._build_repo_context(state, task, task_type)
        if repo_context:
            context_parts.append(repo_context)

        # Add reasoning steps
        reasoning = self._build_reasoning_context(state)
        if reasoning:
            context_parts.append(reasoning)

        # Add reflection notes if requested
        if include_reflection:
            reflection = self._build_reflection_context(state)
            if reflection:
                context_parts.append(reflection)

        return "".join(context_parts)

    def _build_rag_context(self, state: AgentState) -> str:
        """Build context from RAG retrieved documents."""
        retrieved_context = state.get("retrieved_context", [])
        if not retrieved_context:
            return ""

        context = "=== KNOWLEDGE BASE CONTEXT ===\n\n"
        context += "Retrieved information from knowledge base:\n\n"

        for i, chunk in enumerate(retrieved_context, 1):
            chunk_text = chunk.get("content", chunk) if isinstance(chunk, dict) else chunk
            context += f"[Source {i}]:\n{chunk_text}\n\n"

        context += "Use this information to answer the question accurately.\n\n"
        return context

    def _build_repo_context(
        self,
        state: AgentState,
        task: str,
        task_type: str
    ) -> str:
        """Build context from repository analysis."""
        repo_structure = state.get("repo_structure", {})
        dependencies = state.get("dependencies", {})
        architecture = state.get("architecture", {})
        code_files = state.get("code_files", [])

        if not any([repo_structure, dependencies, architecture, code_files]):
            return ""

        context = "=== REPOSITORY ANALYSIS DATA ===\n\n"

        # For LinkedIn posts, use high-level summary
        if task_type == "linkedin_post":
            context += self._build_linkedin_context(
                repo_structure, dependencies, architecture
            )
        else:
            # For code questions, include source code
            if self._is_code_question(task):
                context += self._build_code_context(state, task)

            # Add summary data
            context += self._build_summary_context(
                repo_structure, dependencies, architecture
            )

            # Add code symbols
            context += self._build_code_symbols_context(state)

            # Add verification outputs
            context += self._build_verification_context(state)

        return context

    def _build_linkedin_context(
        self,
        repo_structure: Dict,
        dependencies: Dict,
        architecture: Dict
    ) -> str:
        """Build context specifically for LinkedIn posts."""
        context = "Project Overview:\n\n"

        if repo_structure and repo_structure.get('children'):
            children = repo_structure.get('children', [])
            py_files = [
                item for item in children
                if isinstance(item, dict) and item.get('name', '').endswith('.py')
            ]
            test_files = [
                item for item in children
                if isinstance(item, dict) and 'test' in item.get('name', '').lower()
            ]
            doc_files = [
                item for item in children
                if isinstance(item, dict) and (
                    item.get('name', '').endswith('.md') or
                    'doc' in item.get('name', '').lower()
                )
            ]

            context += f"Project Scope:\n"
            context += f"- Repository contains {len(children)} files and directories\n"
            context += f"- Source files: {len(py_files)} Python files\n"
            context += f"- Test files: {len(test_files)} test files\n"
            context += f"- Documentation: {len(doc_files)} documentation files\n\n"

        if dependencies and dependencies.get('dependencies'):
            deps_list = dependencies.get('dependencies', [])
            key_libs = self._extract_key_libraries(deps_list)

            context += f"Technical Stack ({len(deps_list)} dependencies):\n"
            if key_libs:
                context += f"- AI/ML Libraries: {', '.join(key_libs)}\n"
            context += f"- Total dependencies: {len(deps_list)}\n\n"

        if architecture and architecture.get('modules'):
            modules = architecture.get('modules', [])
            agent_modules = [
                mod for mod in modules
                if isinstance(mod, dict) and 'agent' in str(mod.get('name', '')).lower()
            ]
            test_modules = [
                mod for mod in modules
                if isinstance(mod, dict) and 'test' in str(mod.get('name', '')).lower()
            ]

            context += f"System Architecture:\n"
            context += f"- Modular design with {len(modules)} modules\n"
            context += f"- Agent system modules: {len(agent_modules)}\n"
            context += f"- Test modules: {len(test_modules)}\n"
            context += f"- Clean separation of concerns\n\n"

        return context

    def _build_code_context(self, state: AgentState, task: str) -> str:
        """Build context with source code excerpts."""
        code_files = state.get("code_files", [])
        if not code_files:
            return ""

        print(f"  📄 Detected code-specific question - including source code excerpts")

        context = "Source Code Analysis:\n\n"

        # Find relevant files
        relevant_files = self._find_relevant_files(code_files, task)

        print(f"  📋 Found {len(relevant_files)} relevant files for query")

        # Include top files with excerpts
        max_files = self.config.max_source_files_to_include
        for i, file_info in enumerate(relevant_files[:max_files]):
            file_path = file_info.get('path', '')
            content = file_info.get('content', '')

            print(f"     Including: {file_path.split('/')[-1]}")
            context += f"\n**File {i+1}: {file_path}**\n"

            # Extract relevant sections
            context += self._extract_code_excerpts(content, file_info)

        return context + "\n"

    def _build_summary_context(
        self,
        repo_structure: Dict,
        dependencies: Dict,
        architecture: Dict
    ) -> str:
        """Build summary context."""
        context = "\nRepository Summary:\n"

        if repo_structure and repo_structure.get('children'):
            children = repo_structure.get('children', [])
            context += f"- Total items: {len(children)}\n"
            names = [
                item.get('name', '') for item in children[:10]
                if isinstance(item, dict)
            ]
            context += f"- Key files/directories: {names}\n"

        if dependencies and dependencies.get('dependencies'):
            deps_list = dependencies.get('dependencies', [])
            max_deps = self.config.max_dependencies_to_show
            dep_names = [
                dep.get('name', str(dep)) for dep in deps_list[:max_deps]
                if isinstance(dep, (dict, str))
            ]
            context += f"- Dependencies ({len(deps_list)}): {dep_names}\n"

        if architecture and architecture.get('modules'):
            modules = architecture.get('modules', [])
            max_mods = self.config.max_modules_to_show
            mod_names = [
                mod.get('name', str(mod)) for mod in modules[:max_mods]
                if isinstance(mod, (dict, str))
            ]
            context += f"- Modules ({len(modules)}): {mod_names}\n"

        return context

    def _build_code_symbols_context(self, state: AgentState) -> str:
        """Build context from extracted code symbols."""
        code_symbols = state.get('code_symbols')
        if not code_symbols:
            return ""

        context = f"\n{'='*60}\n"
        context += f"🔥 EXTRACTED CODE SYMBOLS (REAL EVIDENCE FROM CODEBASE)\n"
        context += f"{'='*60}\n"
        context += f"Use these ACTUAL symbols in your analysis - NO HALLUCINATION!\n\n"

        # Summary
        summary = code_symbols.get('summary', {})
        context += f"Summary:\n"
        context += f"- Total Classes: {summary.get('total_classes', 0)}\n"
        context += f"- Total Functions: {summary.get('total_functions', 0)}\n"
        context += f"- Test Functions Found via AST: {summary.get('total_tests', 0)}\n"
        context += f"  ⚠️ NOTE: This is just top-level test functions. Use pytest output for ACTUAL test count!\n\n"

        # Classes
        all_classes = code_symbols.get('all_classes', [])
        if all_classes:
            context += f"📦 Sample Classes (cite these in your analysis):\n"
            max_classes = self.config.max_classes_to_show
            for cls in all_classes[:max_classes]:
                context += f"  - `{cls['name']}` in {cls['file']}:L{cls['line']}\n"
            if len(all_classes) > max_classes:
                context += f"  ... and {len(all_classes) - max_classes} more classes\n"
            context += "\n"

        # Functions
        all_functions = code_symbols.get('all_functions', [])
        if all_functions:
            context += f"⚙️  Sample Functions (cite these in your analysis):\n"
            max_funcs = self.config.max_functions_to_show
            for func in all_functions[:max_funcs]:
                context += f"  - `{func['name']}()` in {func['file']}:L{func['line']}\n"
            if len(all_functions) > max_funcs:
                context += f"  ... and {len(all_functions) - max_funcs} more functions\n"
            context += "\n"

        # Tests
        all_tests = code_symbols.get('all_tests', [])
        if all_tests:
            context += f"🧪 Sample Tests (cite these with :: syntax):\n"
            max_tests = self.config.max_tests_to_show
            for test in all_tests[:max_tests]:
                context += f"  - {test['file']}::{test['name']} (L{test['line']})\n"
            if len(all_tests) > max_tests:
                context += f"  ... and {len(all_tests) - max_tests} more tests\n"
            context += "\n"

        context += f"{'='*60}\n"
        context += f"⚠️ YOU MUST cite these actual symbols in your analysis!\n"
        context += f"⚠️ DO NOT make up class/function names - use the ones above!\n"
        context += f"{'='*60}\n\n"

        return context

    def _build_verification_context(self, state: AgentState) -> str:
        """Build context from verification command outputs."""
        verification_outputs = state.get('verification_outputs')
        if not verification_outputs:
            return ""

        context = f"\n{'='*60}\n"
        context += f"🔥 VERIFICATION OUTPUTS (ACTUAL COMMAND RESULTS)\n"
        context += f"{'='*60}\n"
        context += f"Use these REAL outputs for metrics - DO NOT GUESS!\n\n"

        # Pytest output
        if "pytest_collect" in verification_outputs:
            pytest_out = verification_outputs["pytest_collect"]
            context += f"### 🔥 PYTEST OUTPUT (USE THIS FOR TEST COUNT, NOT AST!):\n"

            match = re.search(r'(\d+) tests? collected', pytest_out)
            if match:
                actual_count = match.group(1)
                context += f"**ACTUAL TEST COUNT: {actual_count} tests collected**\n\n"
                context += f"⚠️ USE THIS NUMBER ({actual_count}), NOT the AST-extracted count!\n"
                context += f"⚠️ AST only finds top-level test functions, pytest finds ALL tests including parametrized\n\n"

            context += f"```\n{pytest_out[:1000]}\n```\n"
            context += f"[Cite as: evidence: pytest --collect-only output]\n\n"

        # Coverage output
        if "coverage_report" in verification_outputs:
            cov_out = verification_outputs["coverage_report"]
            context += f"### 🔥 COVERAGE REPORT:\n"

            if any(word in cov_out for word in ["not installed", "not available", "timed out"]):
                context += f"```\n{cov_out}\n```\n"
                context += f"⚠️ Coverage NOT available - write 'Unknown - {cov_out[:50]}' in report\n\n"
            else:
                match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', cov_out)
                coverage_pct = match.group(1) if match else "Unknown"

                if match:
                    context += f"**ACTUAL COVERAGE: {coverage_pct}%**\n\n"

                context += f"```\n{cov_out[:1500]}\n```\n"
                context += f"[Cite as: {coverage_pct}% coverage [evidence: coverage report]]\n\n"

        # Test file count
        if "test_files_count" in verification_outputs:
            count = verification_outputs["test_files_count"]
            context += f"### Test files count:\n"
            context += f"{count} test files found\n"
            context += f"[Cite as: evidence: find tests command]\n\n"

        context += f"{'='*60}\n"
        context += f"⚠️ USE THESE OUTPUTS - DO NOT INVENT NUMBERS!\n"
        context += f"⚠️ Tag every metric with [evidence: command_name]\n"
        context += f"{'='*60}\n\n"

        return context

    def _build_reasoning_context(self, state: AgentState) -> str:
        """Build context from reasoning steps."""
        reasoning_steps = state.get("reasoning_steps", [])
        if not reasoning_steps:
            return ""

        context = "\nReasoning Steps:\n"
        for step in reasoning_steps[-5:]:
            context += f"- {step}\n"

        return context

    def _build_reflection_context(self, state: AgentState) -> str:
        """Build context from reflection notes."""
        reflection_notes = state.get("reflection_notes", [])
        if not reflection_notes:
            return ""

        context = f"\n{'='*50}\n"
        context += f"SELF-REFLECTION & CRITIQUE (from reflection node):\n"
        context += f"{'='*50}\n"

        for note in reflection_notes:
            context += f"{note}\n"

        context += f"\n⚠️ IMPORTANT: Address the critique above in your response. "
        context += f"If it mentions gaps or missing details, fill those gaps.\n"
        context += f"{'='*50}\n\n"

        return context

    def _is_code_question(self, task: str) -> bool:
        """Check if task is a code-specific question."""
        task_lower = task.lower()
        code_keywords = [
            'where', 'which file', 'how is', 'show me', 'find', 'locate',
            'used in', 'in which', 'implemented', 'code', 'function',
            'class', 'exactly', 'specific', 'import'
        ]
        return any(keyword in task_lower for keyword in code_keywords)

    def _find_relevant_files(
        self,
        code_files: List[Dict],
        query: str
    ) -> List[Dict]:
        """Find relevant source files based on query."""
        query_lower = query.lower()

        # Extract keywords from query
        keywords = []
        if 'langgraph' in query_lower:
            keywords.extend(['langgraph', 'stategraph', 'graph', 'orchestrator'])
        if 'langchain' in query_lower:
            keywords.extend(['langchain', 'chain'])
        if any(word in query_lower for word in ['node', 'nodes']):
            keywords.extend(['node', 'planner', 'generator', 'reasoner'])
        if any(word in query_lower for word in ['evaluation', 'metrics']):
            keywords.extend(['evaluation', 'evaluator', 'metrics'])

        # Score files
        scored_files = []
        for file_info in code_files:
            if file_info.get('error'):
                continue

            content = file_info.get('content', '').lower()
            file_path = file_info.get('path', '')
            file_name = file_path.split('/')[-1].lower()

            score = 0

            # High priority files
            if 'orchestrator' in file_name:
                score += 100
            if any(word in file_name for word in ['planner', 'generator', 'reasoner', 'evaluator']):
                score += 50

            # Check for keywords
            if keywords:
                for keyword in keywords:
                    if keyword in content:
                        score += 10
                    if keyword in file_path.lower():
                        score += 20

            # General relevance
            if any(name in file_path for name in ['agent', 'nodes', 'evaluation']):
                score += 5

            if score > 0:
                scored_files.append((score, file_info))

        # Sort and return
        scored_files.sort(reverse=True, key=lambda x: x[0])
        return [f[1] for f in scored_files]

    def _extract_code_excerpts(
        self,
        content: str,
        file_info: Dict
    ) -> str:
        """Extract relevant code excerpts from file content."""
        lines = content.split('\n')
        excerpts = ""

        # Get imports
        import_lines = []
        max_imports = self.config.max_import_lines_per_file
        for line_num, line in enumerate(lines[:30], 1):
            if 'import' in line or 'from' in line:
                import_lines.append(f"Line {line_num}: {line.strip()}")

        if import_lines:
            excerpts += "Key imports:\n"
            excerpts += "\n".join(import_lines[:max_imports]) + "\n"

        # Get key definitions
        def_lines = []
        max_defs = self.config.max_definitions_per_file
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if (stripped.startswith('def ') or
                stripped.startswith('class ') or
                stripped.startswith('async def ')):
                def_lines.append(f"Line {line_num}: {stripped}")
                if len(def_lines) >= max_defs:
                    break

        if def_lines:
            excerpts += "\nKey definitions:\n"
            excerpts += "\n".join(def_lines) + "\n"

        excerpts += f"\n(Total: {file_info.get('lines', 0)} lines)\n"

        return excerpts

    def _extract_key_libraries(self, deps_list: List) -> List[str]:
        """Extract key AI/ML libraries from dependencies."""
        key_libs = []
        key_terms = ['langgraph', 'langchain', 'openai', 'chromadb', 'azure']

        for dep in deps_list:
            dep_name = dep.get('name', str(dep)) if isinstance(dep, dict) else str(dep)
            if any(key in dep_name.lower() for key in key_terms):
                key_libs.append(dep_name)

        return key_libs
