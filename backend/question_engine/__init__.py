"""
Question Engine Package

AI-powered question generation system using OpenAI GPT-5.2.
Analyzes student code (static + dynamic) and generates
pedagogically valuable comprehension questions.
"""

from question_engine.ai_generator import (
    AIQuestionGenerator,
    GenerationConfig,
    GenerationResult,
    QuestionLevel,
    QuestionType,
    AnswerType,
    QuestionAnswer,
    GeneratedQuestion,
    generate_questions,
    generate_questions_simple,
)

__all__ = [
    "AIQuestionGenerator",
    "GenerationConfig",
    "GenerationResult",
    "QuestionLevel",
    "QuestionType",
    "AnswerType",
    "QuestionAnswer",
    "GeneratedQuestion",
    "generate_questions",
    "generate_questions_simple",
]
