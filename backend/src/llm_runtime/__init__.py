"""LLM-driven agent runtime module.

This module provides the LLM-powered agent decision engine that replaces
the rule-based engine with Gemini-driven decisions for task management.

Public API:
    - LLMAgentEngine: Main engine for processing messages
    - GeminiAdapter: Gemini-specific LLM adapter
    - ToolExecutor: MCP tool execution bridge
    - load_constitution: Helper to load constitution file
"""

from src.llm_runtime.adapter import GeminiAdapter
from src.llm_runtime.engine import LLMAgentEngine, load_constitution
from src.llm_runtime.executor import ToolExecutor

__all__ = [
    "LLMAgentEngine",
    "GeminiAdapter",
    "ToolExecutor",
    "load_constitution",
]
