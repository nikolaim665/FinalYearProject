"""
Question Template System (Compatibility Layer)

This module provides backward compatibility by re-exporting
the data structures from the AI generator.

The actual question generation is now handled by ai_generator.py
using OpenAI GPT-5.2.
"""

# Re-export data structures from AI generator for backward compatibility
from question_engine.ai_generator import (
    QuestionLevel,
    QuestionType,
    AnswerType,
    QuestionAnswer,
    GeneratedQuestion,
)


class TemplateRegistry:
    """
    Minimal template registry for backward compatibility.
    The actual question generation is now handled by AI.
    """

    def __init__(self):
        self.templates = []

    def list_templates(self):
        """Return info about the AI-powered generation system."""
        return [
            {
                'id': 'ai_powered_generator',
                'name': 'AI-Powered Question Generator',
                'description': 'Uses OpenAI GPT-5.2 to generate contextual comprehension questions',
                'type': 'all',
                'level': 'all',
                'difficulty': 'adaptive'
            }
        ]


# Global registry instance
_global_registry = None


def get_registry() -> TemplateRegistry:
    """Get the global template registry (singleton pattern)."""
    global _global_registry
    if _global_registry is None:
        _global_registry = TemplateRegistry()
    return _global_registry
