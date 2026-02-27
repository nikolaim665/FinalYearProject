"""
Question Template System (Compatibility Layer)

The actual question generation is now handled by the LangGraph
multi-agent pipeline in graph.py.

This module provides backward-compatible enums and a minimal
TemplateRegistry for the /health and /templates endpoints.
"""

from enum import Enum


class QuestionLevel(str, Enum):
    ATOM = "atom"
    BLOCK = "block"
    RELATIONAL = "relational"
    MACRO = "macro"


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    NUMERIC = "numeric"


class AnswerType(str, Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"
    CHOICE = "choice"


class TemplateRegistry:
    """
    Minimal template registry.
    The actual question generation is now handled by the LangGraph pipeline.
    """

    def __init__(self):
        self.templates = [
            {
                "id": "langgraph_pipeline",
                "name": "LangGraph Multi-Agent Pipeline",
                "description": (
                    "4-agent pipeline: Analyzer → Question → Answer → Explanation. "
                    "Optional RAG with lecture slides."
                ),
                "type": "multiple_choice",
                "level": "all",
                "difficulty": "adaptive",
            }
        ]

    def list_templates(self):
        """Return info about the LangGraph pipeline."""
        return self.templates


# Global registry instance
_global_registry = None


def get_registry() -> TemplateRegistry:
    """Get the global template registry (singleton pattern)."""
    global _global_registry
    if _global_registry is None:
        _global_registry = TemplateRegistry()
    return _global_registry
