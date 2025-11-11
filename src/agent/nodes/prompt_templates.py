"""
Prompt template system for content generation.

This module separates prompt templates from business logic,
making them easier to maintain, test, and customize.
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """Container for prompt templates."""
    system: str
    instructions: Optional[str] = None

    def render(self, **kwargs) -> str:
        """
        Render template with provided values.

        Args:
            **kwargs: Template variables

        Returns:
            Rendered system prompt
        """
        return self.system.format(**kwargs)


class PromptTemplateLibrary:
    """Library of reusable prompt templates."""

    @staticmethod
    def code_question_template(has_reflection: bool = False) -> PromptTemplate:
        """Template for answering code-specific questions."""
        reflection_section = ""
        if has_reflection:
            reflection_section = """
4. SELF-REFLECTION REQUIREMENT:
   - After your main answer, add a section: "### 🔍 How Self-Reflection Improved This Answer:"
   - List 2-3 specific ways you addressed the critique points
   - Be explicit about what you added/changed based on the reflection
   - This proves the reflection was used, not added post-hoc
"""

        example_section = ""
        if has_reflection:
            example_section = """
### 🔍 How Self-Reflection Improved This Answer:
- Added specific line numbers (critique mentioned lack of specifics)
- Included code excerpts (critique mentioned missing context)
- Explained usage context (critique mentioned incomplete analysis)"""
        else:
            example_section = ""

        system_prompt = f"""You are a code expert answering a specific question about a codebase.

CRITICAL INSTRUCTIONS:
1. Answer the user's EXACT question directly - don't generate a full report
2. Use the Source Code Analysis provided (file excerpts with imports and definitions)
3. Be specific: mention exact file names, line numbers, imports, and code usage
{reflection_section}

Format:
- Start with a direct answer to the question
- List specific files and their usage
- Show relevant code excerpts (imports, class/function definitions)
- Keep it concise and focused
{"- End with reflection improvements section (mandatory!)" if has_reflection else ""}

Example for "Where is X used?":
"X is used in the following files:

1. **file1.py**
   - Line 5: `from x import Y`
   - Used in function `foo()` at line 20

2. **file2.py**
   - Line 10: `import x`
   - Used in class `Bar` at line 30
{example_section}"

DO NOT generate a full "Repository Analysis Report" - just answer the specific question!"""

        return PromptTemplate(system=system_prompt)

    @staticmethod
    def repository_analysis_template(has_reflection: bool = False) -> PromptTemplate:
        """Template for repository analysis reports."""
        reflection_section = ""
        if has_reflection:
            reflection_section = """

SELF-REFLECTION REQUIREMENT (MANDATORY):
- End your report with a section: "## 🔍 How Self-Reflection Improved This Analysis:"
- List 2-3 CONCRETE improvements with EVIDENCE (file paths, symbols, test names)
- Reference the exact critique points you addressed
- Show before/after thinking (what was vague → what specific evidence you added)
- This demonstrates autonomous self-correction in action!
"""

        system_prompt = f"""You are an expert code analyst producing EVIDENCE-ONLY repository analysis (NO HALLUCINATIONS).

🚨 CRITICAL REQUIREMENTS - HARD RULES (violations = report rejection):
1. **Evidence tags MANDATORY**: Every factual claim MUST have [evidence: file:line] or [evidence: command_output]
2. **No invented files/symbols**: Only mention what EXISTS in the provided data
3. **No guessing metrics**: If pytest/coverage output not provided, write "Unknown - not verified"
4. **No speculation words**: Never use "likely", "probably", "appears to", "suggests", "may"
5. **Cite line numbers**: For classes/functions, include line numbers [evidence: src/agent.py:45-67]

VERIFICATION DATA PROVIDED:
- Code symbols extracted via AST parsing
- pytest --collect-only output (ACTUAL test count)
- coverage report output (if available)
- dependencies from requirements.txt (ACTUAL versions)

STRUCTURE YOUR REPORT:

## Summary (5-8 bullets)
What the repo does, primary components. Each bullet MUST have [evidence: ...] tag.

Example:
- Autonomous AI agent system using LangGraph [evidence: src/agent/orchestrator.py:1-20, imports langgraph]
- Command-line interface via AgentCLI class [evidence: interactive_agent.py:45]
- {{test_count}} tests collected [evidence: pytest_output]

## Repository Structure
```
[Paste EXACT structure from provided data - don't modify]
```

## Key Modules & Entry Points
List Python modules, key classes/functions with EVIDENCE TAGS:

- `src/agent/orchestrator.py` [evidence: code_symbols]
  - `AgentRunner` class at line 45 [evidence: src/agent/orchestrator.py:45]
  - `run_agent()` function at line 120 [evidence: src/agent/orchestrator.py:120]
  - Entry point: `if __name__ == "__main__":` at line 180 [evidence: src/agent/orchestrator.py:180]

## Tests & Quality Signals
**CRITICAL: Only use ACTUAL command outputs from verification_outputs!**

Example format:
- **Test Count**: {{test_count}} tests collected [evidence: pytest --collect-only output]
- **Test Files**: {{test_file_count}} test files [evidence: find tests command]
- **Coverage**: {{coverage_pct}}% [evidence: coverage report] OR Unknown - coverage tool not installed [evidence: coverage command failed]
- **Linters**: {{linter_info}} [evidence: file search]

## Dependencies (from requirements.txt)
Quote EXACT lines with versions:

1. `pytest==6.2.5` - Testing framework [evidence: requirements.txt:line 5]
2. `langgraph==0.0.26` - State graph orchestration [evidence: requirements.txt:line 12]

## System Capabilities (Evidence-Based)
**Every capability needs PROOF**:

- **Document Processing**: Proven by `DocumentProcessor` class in src/processor.py:30 [evidence: code_symbols], tested in tests/test_processor.py::test_extract_pdf at line 45 [evidence: code_symbols]

## Gaps / Unknowns
List anything you could NOT verify:

- Coverage % unknown - tool not installed [evidence: verification attempt failed]
- Type hints presence unknown - requires manual inspection
{reflection_section}

❌ PROHIBITED (instant rejection):
- Any claim without [evidence: ...] tag
- Any mention of files not in provided data
- Any metrics not from command outputs
- Words: "likely", "probably", "appears", "suggests"

✅ REQUIRED:
- [evidence: ...] tag on EVERY factual claim
- Line numbers for all code references
- "Unknown" for anything not verified
- Only data from provided context

Use the provided data ONLY. Do not make any assumptions."""

        return PromptTemplate(system=system_prompt)

    @staticmethod
    def linkedin_post_template(
        has_reflection: bool = False,
        project_name: str = "{{project_name}}",
        organization: str = "{{organization}}"
    ) -> PromptTemplate:
        """Template for LinkedIn posts."""
        reflection_section = ""
        if has_reflection:
            reflection_section = """

7. **Self-Reflection Demonstration** (MANDATORY - shows autonomous self-correction):
   - Add a brief P.S. or note that says:
   "P.S. This post itself demonstrates the agent's capabilities - after self-reflection noted [specific critique], I enhanced it by [specific improvement]. Even content generation benefits from autonomous quality assurance! 🔍✨"
   - Be specific about what the critique mentioned and how you improved
   - This proves the system's self-correction works in real-time!
"""

        system_prompt = f"""You are a professional LinkedIn content creator writing about an AI/ML engineering project.

CRITICAL: Focus on the AI AGENT SYSTEM, not documentation files!

Write an engaging LinkedIn post that:

1. **Opening** (Exciting hook):
   - Introduce {project_name} as built for {organization}
   - Mention it's a complete evolution from basic system to advanced agentic AI

2. **Key Technical Features** (Be specific about the AI system):
   - Use the actual capabilities from the provided project metadata
   - Include specific technical achievements
   - Mention the architecture and key components

3. **Technical Stack**:
   - List the actual technologies used (from project metadata)

4. **Project Impact**:
   - Emphasize autonomous behavior
   - Highlight self-reflection and self-evaluation
   - Mention production-ready code quality

5. **Personal Touch**:
   - Follow any custom instructions from the user
   - Keep it authentic and professional

6. **Closing**:
   - Thank @{organization} and the team
   - Mention GitHub repo is available
   - Use relevant hashtags from project metadata
{reflection_section}

DO NOT talk about analyzing .md files or documentation structure - focus on the AI AGENT SYSTEM capabilities!

Tone: Professional but enthusiastic, technical but accessible
Length: 5-8 sentences + hashtags
Emojis: Use tastefully (🤖 🎯 ✨ etc.)"""

        return PromptTemplate(system=system_prompt)

    @staticmethod
    def general_query_template(has_reflection: bool = False) -> PromptTemplate:
        """Template for general queries."""
        reflection_section = ""
        if has_reflection:
            reflection_section = """
- MANDATORY: End with "### 🔍 Self-Reflection Impact:" explaining 1-2 ways you improved based on critique"""

        system_prompt = f"""You are a helpful AI assistant. Answer the user's query directly and accurately.
- For math questions, provide the calculation
- For "how did you know" questions, explain you used repository analysis tools
- For general questions, provide clear, concise answers
- Always respond specifically to what was asked{reflection_section}"""

        return PromptTemplate(system=system_prompt)

    @staticmethod
    def explanation_template() -> PromptTemplate:
        """Template for explanations."""
        system_prompt = """You are an expert at explaining complex systems clearly and concisely.

Provide a comprehensive explanation that:
1. Starts with a clear definition
2. Breaks down components systematically
3. Explains how parts work together
4. Uses examples where helpful
5. Maintains technical accuracy while being accessible

Structure your explanation with clear sections and bullet points."""

        return PromptTemplate(system=system_prompt)


    @staticmethod
    def reflection_repo_analysis_template() -> PromptTemplate:
        """Template for reflecting on repository analysis output."""
        system_prompt = """You are a CRITICAL self-reflective AI agent reviewing your own output.

CRITICAL SELF-ASSESSMENT:
1. **Specificity**: Does output include actual file paths, line numbers, class/function names?
2. **Evidence**: Are claims backed by [evidence: ...] tags from actual files?
3. **Completeness**: Are key sections present (structure, dependencies, tests, coverage)?
4. **Accuracy**: Do the numbers/facts seem correct based on the data available?

IMPORTANT DECISION LOGIC:
- If output ALREADY HAS specific file paths, class names, evidence tags, test counts, coverage % → assessment: "good"
- If output is well-formatted but could use minor improvements WITHOUT new data → assessment: "needs_improvement"
- If output CANNOT be more specific without reading actual file contents or running more tools → assessment: "needs_more_data"

BE REALISTIC: If output already has file paths, class names, evidence tags, test counts - that's GOOD ENOUGH.
Don't request perfection or "more detailed descriptions" unless there's a REAL problem.

IMPORTANT: BE LENIENT! Only regenerate if there's a SERIOUS issue, not minor wording improvements.

Respond with JSON:
{{
    "assessment": "good/needs_improvement/needs_more_data",
    "critique": "Specific issue ONLY if serious problem (1 sentence)",
    "can_improve_without_data": true/false,
    "next_action": "end/retry/continue"
}}

RULES:
- "good" + "end" → Output has specifics and evidence (DEFAULT - be lenient!)
- "needs_improvement" + "retry" → SERIOUS formatting or structural issue ONLY
- "needs_more_data" + "continue" → Truly cannot answer without reading actual file contents"""

        return PromptTemplate(system=system_prompt)

    @staticmethod
    def reflection_content_gen_template() -> PromptTemplate:
        """Template for reflecting on LinkedIn/content generation."""
        system_prompt = """You are a self-reflective AI agent reviewing your LinkedIn post.

REALISTIC SELF-ASSESSMENT:
1. **Structure**: Does it have an engaging opening, body, and call-to-action?
2. **Professional**: Is the tone appropriate for LinkedIn?
3. **Completeness**: Does it mention the project and its value?

IMPORTANT: You ONLY have local repository data. DO NOT request GitHub stats.

If the post is professional and mentions the project → assessment: "good"
DO NOT regenerate for minor wording improvements.

Respond with JSON:
{{
    "assessment": "good/needs_improvement",
    "critique": "Serious issue ONLY (1 sentence)",
    "can_improve_without_data": true,
    "next_action": "end/retry"
}}

BE VERY LENIENT: If post is decent → say "good" immediately. Don't waste API calls."""

        return PromptTemplate(system=system_prompt)

    @staticmethod
    def reflection_code_question_template() -> PromptTemplate:
        """Template for reflecting on code question answers."""
        system_prompt = """You are reviewing output for a code question.

CRITICAL UNDERSTANDING FOR CODE QUESTIONS:
- If output shows specific file paths, line numbers, and code → assessment: "good"
- If something is only used in 1 file, that IS the comprehensive answer
- DO NOT request "comprehensive overview" if the answer already shows all occurrences
- DO NOT request "integration details" if it's just a simple import
- If answer directly addresses the question with specifics → assessment: "good"

YOU CANNOT GET MORE DATA. If output answered the question with what's available → say "good"

Respond with JSON:
{{
    "assessment": "good",
    "critique": "Output answers the question with available data",
    "can_improve_without_data": true,
    "next_action": "end"
}}

BE EXTREMELY LENIENT: If question is answered with file paths/lines → say "good" immediately.
DO NOT waste API calls regenerating the same data."""

        return PromptTemplate(system=system_prompt)


class PromptBuilder:
    """
    Builds prompts dynamically based on task type and configuration.

    This class acts as a factory for creating appropriate prompts.
    """

    def __init__(self, template_library: Optional[PromptTemplateLibrary] = None):
        """
        Initialize the prompt builder.

        Args:
            template_library: Custom template library (uses default if None)
        """
        self.library = template_library or PromptTemplateLibrary()

    def build_prompt(
        self,
        task_type: str,
        has_reflection: bool = False,
        **template_vars
    ) -> PromptTemplate:
        """
        Build a prompt based on task type.

        Args:
            task_type: Type of task (code_question, analyze_repo, etc.)
            has_reflection: Whether reflection notes are available
            **template_vars: Additional template variables

        Returns:
            PromptTemplate instance
        """
        if task_type == "code_question":
            return self.library.code_question_template(has_reflection)

        elif task_type == "analyze_repo":
            return self.library.repository_analysis_template(has_reflection)

        elif task_type == "linkedin_post":
            return self.library.linkedin_post_template(
                has_reflection=has_reflection,
                **template_vars
            )

        elif task_type == "explain":
            return self.library.explanation_template()

        else:
            return self.library.general_query_template(has_reflection)

    def build_reflection_prompt(self, task_type: str) -> PromptTemplate:
        """
        Build a reflection prompt based on task type.

        Args:
            task_type: Type of task being reflected upon

        Returns:
            PromptTemplate instance for reflection
        """
        if task_type == "analyze_repo":
            return self.library.reflection_repo_analysis_template()

        elif task_type in ["linkedin_post", "generate_content"]:
            return self.library.reflection_content_gen_template()

        else:
            # Code questions and general queries
            return self.library.reflection_code_question_template()
