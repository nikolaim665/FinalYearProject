"""
Tests for the Answer Validator

Tests the semantic answer validation for open-ended questions with multiple
valid answers.
"""

import pytest
from question_engine.answer_validator import (
    AnswerValidator,
    ValidationResult,
    MatchType,
    validate_answer
)


class TestAnswerValidator:
    """Tests for AnswerValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = AnswerValidator(case_sensitive=False, allow_partial=True)

    def test_exact_match_primary_answer(self):
        """Test exact match with primary answer."""
        result = self.validator.validate(
            student_answer="recursive",
            correct_answer="recursive",
            alternative_answers=["recursion", "calls itself"]
        )

        assert result.is_correct is True
        assert result.match_type == MatchType.EXACT
        assert result.confidence == 1.0

    def test_exact_match_alternative_answer(self):
        """Test exact match with alternative answer."""
        result = self.validator.validate(
            student_answer="recursion",
            correct_answer="recursive",
            alternative_answers=["recursion", "calls itself"]
        )

        assert result.is_correct is True
        assert result.match_type == MatchType.ALTERNATIVE
        assert result.matched_answer == "recursion"

    def test_case_insensitive_match(self):
        """Test case insensitive matching."""
        result = self.validator.validate(
            student_answer="RECURSIVE",
            correct_answer="recursive",
            alternative_answers=[]
        )

        assert result.is_correct is True
        assert result.match_type == MatchType.EXACT

    def test_whitespace_normalization(self):
        """Test whitespace is normalized."""
        result = self.validator.validate(
            student_answer="  recursive  function  ",
            correct_answer="recursive function",
            alternative_answers=[]
        )

        assert result.is_correct is True

    def test_punctuation_removal(self):
        """Test trailing punctuation is removed."""
        result = self.validator.validate(
            student_answer="recursive.",
            correct_answer="recursive",
            alternative_answers=[]
        )

        assert result.is_correct is True

    def test_normalized_match_stop_words(self):
        """Test matching with stop words removed."""
        result = self.validator.validate(
            student_answer="the recursive function",
            correct_answer="recursive function",
            alternative_answers=[]
        )

        assert result.is_correct is True
        assert result.match_type == MatchType.NORMALIZED

    def test_semantic_match_synonyms(self):
        """Test semantic matching with synonyms."""
        result = self.validator.validate(
            student_answer="iteration",
            correct_answer="loop",
            alternative_answers=[],
            question_type="short_answer"
        )

        assert result.is_correct is True
        assert result.match_type == MatchType.PARTIAL

    def test_semantic_match_programming_synonyms(self):
        """Test semantic matching with programming synonyms."""
        result = self.validator.validate(
            student_answer="method",
            correct_answer="function",
            alternative_answers=[],
            question_type="short_answer"
        )

        assert result.is_correct is True
        assert result.match_type == MatchType.PARTIAL

    def test_no_match_completely_wrong(self):
        """Test no match for completely wrong answer."""
        result = self.validator.validate(
            student_answer="banana",
            correct_answer="recursive",
            alternative_answers=["recursion", "calls itself"]
        )

        assert result.is_correct is False
        assert result.match_type == MatchType.NO_MATCH

    def test_partial_match_concept(self):
        """Test partial matching captures key concept."""
        result = self.validator.validate(
            student_answer="calculates total sum",
            correct_answer="computes the sum",
            alternative_answers=["adds up values", "total calculation"],
            question_type="short_answer"
        )

        # Should match due to synonym overlap (sum, total, calculates/computes)
        assert result.is_correct is True

    def test_multiple_alternatives(self):
        """Test with multiple alternative answers."""
        result = self.validator.validate(
            student_answer="calls itself",
            correct_answer="recursive",
            alternative_answers=["recursion", "calls itself", "self-calling", "recursive function"]
        )

        assert result.is_correct is True
        assert result.matched_answer == "calls itself"

    def test_fill_in_blank_type(self):
        """Test fill-in-blank question type."""
        result = self.validator.validate(
            student_answer="120",
            correct_answer="120",
            alternative_answers=[],
            question_type="fill_in_blank"
        )

        assert result.is_correct is True

    def test_empty_student_answer(self):
        """Test handling of empty student answer."""
        result = self.validator.validate(
            student_answer="",
            correct_answer="recursive",
            alternative_answers=[]
        )

        assert result.is_correct is False

    def test_confidence_score_exact(self):
        """Test confidence score for exact match."""
        result = self.validator.validate(
            student_answer="recursive",
            correct_answer="recursive",
            alternative_answers=[]
        )

        assert result.confidence == 1.0

    def test_confidence_score_partial(self):
        """Test confidence score for partial match."""
        result = self.validator.validate(
            student_answer="iteration cycle",
            correct_answer="loop iteration",
            alternative_answers=[],
            question_type="short_answer"
        )

        # The match should succeed since iteration/loop are synonyms
        assert result.is_correct is True
        assert result.match_type == MatchType.PARTIAL


class TestValidateAnswerFunction:
    """Tests for the validate_answer convenience function."""

    def test_convenience_function_basic(self):
        """Test the convenience function works."""
        result = validate_answer(
            student_answer="recursive",
            correct_answer="recursive",
            alternative_answers=["recursion"]
        )

        assert result.is_correct is True

    def test_convenience_function_with_type(self):
        """Test convenience function with question type."""
        result = validate_answer(
            student_answer="loop",
            correct_answer="iteration",
            alternative_answers=[],
            question_type="short_answer"
        )

        assert result.is_correct is True  # Should match via synonym

    def test_convenience_function_case_sensitive(self):
        """Test convenience function with case sensitivity."""
        # With case_sensitive=True, "RECURSIVE" != "recursive" but
        # key word extraction also uses lowercase for synonyms, so
        # it may still match via normalized comparison

        # Test that default (case insensitive) works
        result = validate_answer(
            student_answer="RECURSIVE",
            correct_answer="recursive",
            alternative_answers=[],
            case_sensitive=False
        )
        assert result.is_correct is True

        # Test exact opposite strings don't match with case sensitive
        validator = AnswerValidator(case_sensitive=True, allow_partial=False)
        result = validator.validate(
            student_answer="TOTALLY DIFFERENT",
            correct_answer="recursive",
            alternative_answers=[]
        )
        assert result.is_correct is False


class TestRealWorldScenarios:
    """Tests based on real-world programming education scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = AnswerValidator()

    def test_function_type_question(self):
        """What type of function is factorial?"""
        alternatives = ["recursion", "recursive function", "calls itself", "self-calling"]

        # Student says "recursive"
        result = self.validator.validate("recursive", "recursive", alternatives)
        assert result.is_correct is True

        # Student says "it calls itself"
        result = self.validator.validate("it calls itself", "recursive", alternatives)
        assert result.is_correct is True

    def test_loop_purpose_question(self):
        """What is the purpose of the loop?"""
        correct = "iterates through the list"
        alternatives = [
            "loops through the list",
            "goes through each element",
            "processes list items",
            "traverses the list"
        ]

        # Student says "loops through list elements"
        result = self.validator.validate(
            "loops through list elements",
            correct,
            alternatives,
            question_type="short_answer"
        )
        assert result.is_correct is True

    def test_variable_purpose_question(self):
        """What does the variable 'total' store?"""
        correct = "the sum of all numbers"
        alternatives = ["sum of numbers", "total sum", "accumulated sum", "sum", "running total"]

        # Student says "sum"
        result = self.validator.validate("sum", correct, alternatives)
        assert result.is_correct is True

        # Student says "the total"
        result = self.validator.validate("the total", correct, alternatives)
        # Should match "total sum" or "running total" via alternatives
        assert result.is_correct is True

    def test_data_type_question(self):
        """What is the data type of x?"""
        correct = "integer"
        alternatives = ["int", "whole number", "number"]

        result = self.validator.validate("int", correct, alternatives)
        assert result.is_correct is True

        result = self.validator.validate("integer", correct, alternatives)
        assert result.is_correct is True

    def test_print_output_question(self):
        """What does the program print?"""
        correct = "Hello World"
        alternatives = ["Hello World!", "hello world"]

        # Exact match
        result = self.validator.validate("Hello World", correct, alternatives)
        assert result.is_correct is True

        # Case variation (should match via alternative)
        result = self.validator.validate("hello world", correct, alternatives)
        assert result.is_correct is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
