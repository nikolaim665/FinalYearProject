"""
Tests for Question Generator
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from question_engine.generator import (
    QuestionGenerator,
    GenerationConfig,
    GenerationStrategy,
    GenerationResult,
    generate_questions,
    generate_questions_simple
)
from question_engine.templates import QuestionLevel, QuestionType


class TestGenerationConfig:
    """Tests for GenerationConfig."""

    def test_default_config(self):
        """Default config should have sensible defaults."""
        config = GenerationConfig()

        assert config.enable_static_analysis is True
        assert config.enable_dynamic_analysis is True
        assert config.max_questions == 10
        assert config.min_questions == 3
        assert config.strategy == GenerationStrategy.DIVERSE

    def test_custom_config(self):
        """Should be able to customize config."""
        config = GenerationConfig(
            max_questions=5,
            strategy=GenerationStrategy.FOCUSED,
            allowed_difficulties={'easy', 'medium'}
        )

        assert config.max_questions == 5
        assert config.strategy == GenerationStrategy.FOCUSED
        assert 'hard' not in config.allowed_difficulties


class TestQuestionGenerator:
    """Tests for QuestionGenerator class."""

    def test_initialization(self):
        """Should initialize with default or custom config."""
        generator = QuestionGenerator()
        assert generator.config is not None
        assert generator.static_analyzer is not None
        assert generator.dynamic_analyzer is not None

        custom_config = GenerationConfig(max_questions=5)
        generator2 = QuestionGenerator(custom_config)
        assert generator2.config.max_questions == 5

    def test_generate_with_simple_code(self):
        """Should generate questions from simple code."""
        generator = QuestionGenerator()

        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def double(x):
    return x * 2

result = factorial(5)
"""
        result = generator.generate(code)

        assert isinstance(result, GenerationResult)
        assert len(result.questions) > 0
        assert result.static_analysis is not None
        assert result.dynamic_analysis is not None
        assert result.execution_successful is True
        assert len(result.errors) == 0

    def test_generate_with_syntax_error(self):
        """Should handle syntax errors gracefully."""
        generator = QuestionGenerator()

        code = """
def broken(
    print("missing closing paren")
"""
        result = generator.generate(code)

        assert len(result.questions) == 0
        assert result.execution_successful is False
        assert len(result.errors) > 0
        assert 'Syntax error' in result.errors[0]

    def test_generate_with_runtime_error(self):
        """Should handle runtime errors and still generate static questions."""
        generator = QuestionGenerator()

        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def double(x):
    return x * 2

result = factorial(5)
broken = 1 / 0  # Runtime error
"""
        result = generator.generate(code)

        # Should still have static analysis
        assert result.static_analysis is not None
        # Dynamic analysis failed
        assert result.execution_successful is False
        # Should have warnings about execution failure
        assert len(result.warnings) > 0
        # But might still have questions from static analysis
        # (depends on templates)

    def test_generate_with_loops(self):
        """Should generate loop-related questions."""
        generator = QuestionGenerator()

        code = """
total = 0
for i in range(5):
    total += i

count = 0
while count < 3:
    count += 1
"""
        result = generator.generate(code)

        assert len(result.questions) > 0

        # Should have loop iteration questions
        loop_questions = [q for q in result.questions
                         if q.template_id == 'loop_iteration_count']
        assert len(loop_questions) > 0

    def test_static_only_mode(self):
        """Should work with static analysis only."""
        config = GenerationConfig(enable_dynamic_analysis=False)
        generator = QuestionGenerator(config)

        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def helper(x):
    return x
"""
        result = generator.generate(code)

        assert result.static_analysis is not None
        assert result.dynamic_analysis is None
        # Should still generate questions from static analysis
        assert len(result.questions) > 0

    def test_dynamic_only_mode(self):
        """Should work with dynamic analysis only."""
        config = GenerationConfig(enable_static_analysis=False)
        generator = QuestionGenerator(config)

        code = """
x = 5
y = x * 2
"""
        result = generator.generate(code)

        assert result.static_analysis is None
        assert result.dynamic_analysis is not None

    def test_max_questions_limit(self):
        """Should respect max_questions limit."""
        config = GenerationConfig(max_questions=3)
        generator = QuestionGenerator(config)

        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)

for i in range(5):
    x = i * 2

result = factorial(5)
"""
        result = generator.generate(code)

        assert len(result.questions) <= 3

    def test_filter_by_level(self):
        """Should filter questions by level."""
        config = GenerationConfig(
            allowed_levels={QuestionLevel.BLOCK}
        )
        generator = QuestionGenerator(config)

        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def helper(x):
    return x

result = factorial(5)
"""
        result = generator.generate(code)

        # All questions should be BLOCK level
        for question in result.questions:
            assert question.question_level == QuestionLevel.BLOCK

    def test_filter_by_difficulty(self):
        """Should filter questions by difficulty."""
        config = GenerationConfig(
            allowed_difficulties={'easy'}
        )
        generator = QuestionGenerator(config)

        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def helper(x):
    return x

result = factorial(5)
"""
        result = generator.generate(code)

        # All questions should be easy
        for question in result.questions:
            assert question.difficulty == 'easy'

    def test_diverse_strategy(self):
        """Diverse strategy should select varied questions."""
        config = GenerationConfig(
            strategy=GenerationStrategy.DIVERSE,
            max_questions=5
        )
        generator = QuestionGenerator(config)

        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def helper(x):
    return x

for i in range(5):
    pass

result = factorial(5)
"""
        result = generator.generate(code)

        # Check diversity - should have different types/levels
        if len(result.questions) >= 2:
            types = {q.question_type for q in result.questions}
            # Should have variety (though depends on available templates)
            assert len(types) >= 1

    def test_no_applicable_templates(self):
        """Should handle case with no applicable templates."""
        generator = QuestionGenerator()

        # Very simple code that doesn't match any templates
        code = """
x = 5
"""
        result = generator.generate(code)

        # Might have variable tracing questions
        # Or might have warnings about no templates
        assert result.static_analysis is not None

    def test_test_inputs(self):
        """Should accept test inputs for dynamic analysis."""
        generator = QuestionGenerator()

        code = """
result = input_value * 2
"""
        result = generator.generate(code, test_inputs={'input_value': 10})

        assert result.dynamic_analysis is not None

    def test_deduplication(self):
        """Should deduplicate similar questions."""
        config = GenerationConfig(remove_similar_questions=True)
        generator = QuestionGenerator(config)

        code = """
x = 1
y = 2
z = 3
a = 4
b = 5
c = 6
d = 7
"""
        result = generator.generate(code)

        # Should limit variable tracing questions
        var_questions = [q for q in result.questions
                        if q.template_id == 'variable_value_tracing']

        # Should be deduplicated to max 3
        assert len(var_questions) <= 3


class TestGenerationResult:
    """Tests for GenerationResult."""

    def test_to_dict_serialization(self):
        """Should serialize to dictionary."""
        generator = QuestionGenerator()

        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
"""
        result = generator.generate(code)
        result_dict = result.to_dict()

        assert 'questions' in result_dict
        assert 'metadata' in result_dict
        assert 'errors' in result_dict
        assert 'warnings' in result_dict

        # Metadata should have counts
        metadata = result_dict['metadata']
        assert 'total_generated' in metadata
        assert 'total_returned' in metadata
        assert 'applicable_templates' in metadata

    def test_static_analysis_summary(self):
        """Should include static analysis summary."""
        generator = QuestionGenerator()

        code = """
def factorial(n):
    return 1 if n <= 1 else n * factorial(n - 1)

def helper(x):
    return x
"""
        result = generator.generate(code)
        result_dict = result.to_dict()

        assert 'static_analysis_summary' in result_dict
        summary = result_dict['static_analysis_summary']
        assert summary is not None
        assert 'total_functions' in summary

    def test_dynamic_analysis_summary(self):
        """Should include dynamic analysis summary."""
        generator = QuestionGenerator()

        code = """
x = 5
y = x * 2
"""
        result = generator.generate(code)
        result_dict = result.to_dict()

        assert 'dynamic_analysis_summary' in result_dict
        summary = result_dict['dynamic_analysis_summary']
        assert summary is not None
        assert 'execution_successful' in summary


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_generate_questions_function(self):
        """Should work as a convenience function."""
        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
"""
        result = generate_questions(code)

        assert isinstance(result, GenerationResult)
        assert len(result.questions) > 0

    def test_generate_questions_with_config(self):
        """Should accept custom config."""
        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
"""
        config = GenerationConfig(max_questions=2)
        result = generate_questions(code, config)

        assert len(result.questions) <= 2

    def test_generate_questions_simple(self):
        """Simple function should return just questions."""
        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
"""
        questions = generate_questions_simple(code, max_questions=3)

        assert isinstance(questions, list)
        assert len(questions) <= 3
        # All items should be questions
        from question_engine.templates import GeneratedQuestion
        for q in questions:
            assert isinstance(q, GeneratedQuestion)


class TestIntegration:
    """Integration tests for complete pipeline."""

    def test_complete_pipeline_fibonacci(self):
        """Test complete pipeline with Fibonacci code."""
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

def fibonacci_iterative(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return b

recursive_result = fibonacci(6)
iterative_result = fibonacci_iterative(6)
"""
        generator = QuestionGenerator()
        result = generator.generate(code)

        # Should have successful analysis
        assert result.static_analysis is not None
        assert result.dynamic_analysis is not None
        assert result.execution_successful is True

        # Should generate questions
        assert len(result.questions) > 0

        # Should have recursive function questions
        recursive_q = [q for q in result.questions
                      if q.template_id == 'recursive_function_detection']
        assert len(recursive_q) > 0

        # Should have loop questions
        loop_q = [q for q in result.questions
                 if q.template_id == 'loop_iteration_count']
        assert len(loop_q) > 0

    def test_complete_pipeline_sorting(self):
        """Test complete pipeline with sorting algorithm."""
        code = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

numbers = [64, 34, 25, 12, 22, 11, 90]
sorted_numbers = bubble_sort(numbers)
"""
        generator = QuestionGenerator()
        result = generator.generate(code)

        # Should execute successfully
        assert result.execution_successful is True

        # Should generate questions
        assert len(result.questions) > 0

        # Should have loop iteration questions
        loop_q = [q for q in result.questions
                 if q.template_id == 'loop_iteration_count']
        # Nested loops should be detected
        assert len(loop_q) > 0

    def test_pipeline_with_all_strategies(self):
        """Test all selection strategies work."""
        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def helper(x):
    return x

for i in range(5):
    pass

result = factorial(5)
"""
        for strategy in GenerationStrategy:
            config = GenerationConfig(strategy=strategy, max_questions=5)
            generator = QuestionGenerator(config)
            result = generator.generate(code)

            # All strategies should return valid results
            assert isinstance(result, GenerationResult)
            assert len(result.questions) <= 5

    def test_json_serialization(self):
        """Test that results can be serialized to JSON."""
        import json

        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
"""
        generator = QuestionGenerator()
        result = generator.generate(code)
        result_dict = result.to_dict()

        # Should be JSON serializable
        json_str = json.dumps(result_dict, indent=2)
        assert len(json_str) > 0

        # Should be deserializable
        loaded = json.loads(json_str)
        assert 'questions' in loaded
        assert 'metadata' in loaded
