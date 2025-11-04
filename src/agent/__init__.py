"""
Agent system for v2.0 agentic AI capabilities.

This module provides the core agent orchestration using LangGraph,
including state management, node definitions, and workflow coordination.

Components:
    - state: AgentState TypedDict and state management
    - orchestrator: LangGraph workflow and agent execution
    - nodes: Individual agent node implementations

Example:
    >>> from src.agent.orchestrator import run_agent
    >>> result = run_agent("Analyze this repository")
    >>> print(result["final_output"])
"""

__version__ = "2.0.0"
__all__ = ["state", "orchestrator", "nodes"]
