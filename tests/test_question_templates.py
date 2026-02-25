"""
Tests for Question Template System

Tests the compatibility layer (templates.py) and the core data structures
exported from the AI generator. The full template class system was replaced
by AI-powered generation (ai_generator.py).
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from question_engine.templates import (
    QuestionLevel,
    QuestionType,
    AnswerType,
    GeneratedQuestion,
    QuestionAnswer,
    TemplateRegistry,
    get_registry,
)


class TestQuestionTypeEnum:
    """Tests for the QuestionType enum."""

    def test_multiple_choice_exists(self):
        assert QuestionType.MULTIPLE_CHOICE.value == "multiple_choice"

    def test_true_false_exists(self):
        assert QuestionType.TRUE_FALSE.value == "true_false"

    def test_numeric_exists(self):
        assert QuestionType.NUMERIC.value == "numeric"

    def test_code_selection_exists(self):
        assert QuestionType.CODE_SELECTION.value == "code_selection"

    def test_fill_in_blank_removed(self):
        """fill_in_blank should no longer be a valid question type."""
        type_values = [qt.value for qt in QuestionType]
        assert "fill_in_blank" not in type_values

    def test_short_answer_removed(self):
        """short_answer should no longer be a valid question type."""
        type_values = [qt.value for qt in QuestionType]
        assert "short_answer" not in type_values


class TestQuestionLevelEnum:
    """Tests for the QuestionLevel enum."""

    def test_all_levels_exist(self):
        assert QuestionLevel.ATOM.value == "atom"
        assert QuestionLevel.BLOCK.value == "block"
        assert QuestionLevel.RELATIONAL.value == "relational"
        assert QuestionLevel.MACRO.value == "macro"


class TestAnswerTypeEnum:
    """Tests for the AnswerType enum."""

    def test_all_answer_types_exist(self):
        assert AnswerType.STATIC.value == "static"
        assert AnswerType.DYNAMIC.value == "dynamic"
        assert AnswerType.HYBRID.value == "hybrid"
        assert AnswerType.AI.value == "ai"


class TestGeneratedQuestion:
    """Tests for GeneratedQuestion dataclass."""

    def _make_question(self, **kwargs):
        defaults = dict(
            template_id="test_template",
            question_text="What is the value of x?",
            question_type=QuestionType.NUMERIC,
            question_level=QuestionLevel.ATOM,
            answer_type=AnswerType.DYNAMIC,
            correct_answer=42,
        )
        defaults.update(kwargs)
        return GeneratedQuestion(**defaults)

    def test_creation_with_required_fields(self):
        q = self._make_question()
        assert q.template_id == "test_template"
        assert q.correct_answer == 42

    def test_default_empty_collections(self):
        q = self._make_question()
        assert q.answer_choices == []
        assert q.alternative_answers == []
        assert q.context == {}

    def test_to_dict_contains_required_keys(self):
        q = self._make_question()
        d = q.to_dict()
        for key in ("template_id", "question_text", "question_type",
                    "question_level", "correct_answer", "answer_choices"):
            assert key in d

    def test_to_dict_serialises_enums_as_strings(self):
        q = self._make_question()
        d = q.to_dict()
        assert d["question_type"] == "numeric"
        assert d["question_level"] == "atom"

    def test_to_dict_with_answer_choices(self):
        choices = [
            QuestionAnswer(text="5", is_correct=True, explanation="Correct"),
            QuestionAnswer(text="10", is_correct=False, explanation="Wrong"),
        ]
        q = self._make_question(
            question_type=QuestionType.MULTIPLE_CHOICE,
            answer_choices=choices,
        )
        d = q.to_dict()
        assert len(d["answer_choices"]) == 2
        assert d["answer_choices"][0]["is_correct"] is True

    def test_multiple_choice_question(self):
        choices = [
            QuestionAnswer(text="factorial", is_correct=True),
            QuestionAnswer(text="helper", is_correct=False),
        ]
        q = self._make_question(
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_level=QuestionLevel.BLOCK,
            answer_type=AnswerType.STATIC,
            correct_answer="factorial",
            answer_choices=choices,
        )
        assert q.question_type == QuestionType.MULTIPLE_CHOICE
        assert len(q.answer_choices) == 2

    def test_true_false_question(self):
        q = self._make_question(
            question_type=QuestionType.TRUE_FALSE,
            correct_answer="true",
        )
        assert q.question_type == QuestionType.TRUE_FALSE

    def test_numeric_question(self):
        q = self._make_question(
            question_type=QuestionType.NUMERIC,
            correct_answer=5,
        )
        assert q.question_type == QuestionType.NUMERIC
        assert q.correct_answer == 5


class TestTemplateRegistry:
    """Tests for the (compatibility-layer) TemplateRegistry."""

    def test_registry_creates_successfully(self):
        registry = TemplateRegistry()
        assert registry is not None

    def test_list_templates_returns_list(self):
        registry = TemplateRegistry()
        templates = registry.list_templates()
        assert isinstance(templates, list)
        assert len(templates) >= 1

    def test_list_templates_entry_has_expected_keys(self):
        registry = TemplateRegistry()
        for entry in registry.list_templates():
            assert "id" in entry
            assert "name" in entry

    def test_get_registry_returns_singleton(self):
        r1 = get_registry()
        r2 = get_registry()
        assert r1 is r2

    def test_get_registry_returns_template_registry(self):
        registry = get_registry()
        assert isinstance(registry, TemplateRegistry)
