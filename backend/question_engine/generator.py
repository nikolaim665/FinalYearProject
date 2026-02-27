"""
Question Generator (Compatibility Shim)

The question generation is now handled by the LangGraph multi-agent pipeline.
This module provides a thin compatibility shim for any code that still imports
from question_engine.generator.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Set, Any


class GenerationStrategy(str, Enum):
    ALL = "all"
    DIVERSE = "diverse"
    FOCUSED = "focused"
    ADAPTIVE = "adaptive"


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


@dataclass
class GenerationConfig:
    max_questions: int = 10
    enable_auto_driver: bool = True
    enable_caching: bool = True
    include_levels: List[str] = field(default_factory=list)
    include_types: List[str] = field(default_factory=list)
    include_difficulties: List[str] = field(default_factory=list)
    allowed_levels: Set[QuestionLevel] = field(default_factory=set)
    allowed_difficulties: Set[str] = field(default_factory=set)


class QuestionGenerator:
    """Compat shim — delegates to run_pipeline."""

    def __init__(self, config: Optional[GenerationConfig] = None):
        self.config = config or GenerationConfig()

    def generate(self, source_code: str, test_inputs: Optional[Any] = None):
        from question_engine.graph import run_pipeline
        cfg = {
            "max_questions": self.config.max_questions,
            "enable_auto_driver": self.config.enable_auto_driver,
            "enable_caching": self.config.enable_caching,
            "include_levels": self.config.include_levels,
            "include_types": self.config.include_types,
            "include_difficulties": self.config.include_difficulties,
        }
        return run_pipeline(source_code=source_code, max_questions=self.config.max_questions, config=cfg)
