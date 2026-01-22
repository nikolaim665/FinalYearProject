"""
Question Generator (Compatibility Layer)

This module provides backward compatibility by re-exporting
from the AI generator.

The actual question generation is now handled by ai_generator.py
using OpenAI GPT-5.2.
"""

# Re-export everything from AI generator for backward compatibility
from question_engine.ai_generator import (
    # Classes
    AIQuestionGenerator as QuestionGenerator,
    GenerationConfig,
    GenerationResult,
    QuestionLevel,
    QuestionType,
    AnswerType,
    QuestionAnswer,
    GeneratedQuestion,
    # Functions
    generate_questions,
    generate_questions_simple,
)

# Legacy enum for backward compatibility
from enum import Enum


class GenerationStrategy(Enum):
    """
    Legacy strategy enum.
    Note: With AI generation, the strategy is handled by the prompt.
    These are kept for API compatibility.
    """
    ALL = "all"
    DIVERSE = "diverse"
    FOCUSED = "focused"
    ADAPTIVE = "adaptive"
