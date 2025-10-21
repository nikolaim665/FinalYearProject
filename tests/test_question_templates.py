"""
Tests for Question Template System
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from analyzers.static_analyzer import StaticAnalyzer
from analyzers.dynamic_analyzer import DynamicAnalyzer
from question_engine.templates import (
    QuestionTemplate,
    QuestionLevel,
    QuestionType,
    AnswerType,
    RecursiveFunctionTemplate,
    VariableValueTemplate,
    LoopIterationCountTemplate,
    TemplateRegistry,
    get_registry
)


class TestRecursiveFunctionTemplate:
    """Tests for RecursiveFunctionTemplate."""

    def test_is_applicable_with_multiple_functions(self):
        """Template should be applicable when there are 2+ functions."""
        template = RecursiveFunctionTemplate()
        static_analysis = {
            'functions': [
                {'name': 'factorial', 'is_recursive': True},
                {'name': 'helper', 'is_recursive': False}
            ]
        }
        assert template.is_applicable(static_analysis) is True

    def test_is_not_applicable_with_single_function(self):
        """Template should not be applicable with only 1 function."""
        template = RecursiveFunctionTemplate()
        static_analysis = {
            'functions': [
                {'name': 'factorial', 'is_recursive': True}
            ]
        }
        assert template.is_applicable(static_analysis) is False

    def test_is_not_applicable_with_no_functions(self):
        """Template should not be applicable with no functions."""
        template = RecursiveFunctionTemplate()
        static_analysis = {'functions': []}
        assert template.is_applicable(static_analysis) is False

    def test_generate_question_with_recursive_function(self):
        """Should generate question identifying recursive functions."""
        template = RecursiveFunctionTemplate()

        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def double(x):
    return x * 2
"""
        analyzer = StaticAnalyzer()
        static_analysis = analyzer.analyze(code)

        questions = template.generate_questions(static_analysis)

        assert len(questions) == 1
        question = questions[0]

        assert question.template_id == 'recursive_function_detection'
        assert 'recursive' in question.question_text.lower()
        assert question.question_type == QuestionType.MULTIPLE_CHOICE
        assert question.question_level == QuestionLevel.BLOCK

        # Check answer choices
        assert len(question.answer_choices) == 2
        factorial_choice = next(c for c in question.answer_choices if c.text == 'factorial')
        double_choice = next(c for c in question.answer_choices if c.text == 'double')

        assert factorial_choice.is_correct is True
        assert double_choice.is_correct is False

    def test_generate_question_with_no_recursive_functions(self):
        """Should handle case with no recursive functions."""
        template = RecursiveFunctionTemplate()

        code = """
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
"""
        analyzer = StaticAnalyzer()
        static_analysis = analyzer.analyze(code)

        questions = template.generate_questions(static_analysis)

        assert len(questions) == 1
        question = questions[0]

        # All choices should be marked as incorrect
        assert all(not choice.is_correct for choice in question.answer_choices)
        assert "None of the functions are recursive" in question.correct_answer


class TestVariableValueTemplate:
    """Tests for VariableValueTemplate."""

    def test_is_applicable_with_successful_execution(self):
        """Template should be applicable when code executes successfully."""
        template = VariableValueTemplate()
        static_analysis = {}
        dynamic_analysis = {
            'execution_successful': True,
            'variable_snapshots': [
                {'name': 'x', 'value': 10, 'line': 1}
            ]
        }
        assert template.is_applicable(static_analysis, dynamic_analysis) is True

    def test_is_not_applicable_without_dynamic_analysis(self):
        """Template should not be applicable without dynamic analysis."""
        template = VariableValueTemplate()
        static_analysis = {}
        assert template.is_applicable(static_analysis, None) is False

    def test_is_not_applicable_with_failed_execution(self):
        """Template should not be applicable if execution failed."""
        template = VariableValueTemplate()
        static_analysis = {}
        dynamic_analysis = {
            'execution_successful': False,
            'variable_snapshots': []
        }
        assert template.is_applicable(static_analysis, dynamic_analysis) is False

    def test_generate_questions_with_variables(self):
        """Should generate questions about variable values."""
        template = VariableValueTemplate()

        code = """
x = 5
y = x * 2
z = y + 3
"""
        static_analyzer = StaticAnalyzer()
        dynamic_analyzer = DynamicAnalyzer()

        static_analysis = static_analyzer.analyze(code)
        dynamic_analysis = dynamic_analyzer.analyze(code)

        questions = template.generate_questions(static_analysis, dynamic_analysis)

        assert len(questions) > 0

        for question in questions:
            assert question.template_id == 'variable_value_tracing'
            assert 'value' in question.question_text.lower()
            assert question.question_type == QuestionType.FILL_IN_BLANK
            assert question.correct_answer is not None
            assert 'variable_name' in question.context
            assert 'line_number' in question.context

    def test_generate_questions_with_function_scope(self):
        """Should generate questions about variables in function scope."""
        template = VariableValueTemplate()

        code = """
def calculate(n):
    result = n * 2
    return result

output = calculate(5)
"""
        static_analyzer = StaticAnalyzer()
        dynamic_analyzer = DynamicAnalyzer()

        static_analysis = static_analyzer.analyze(code)
        dynamic_analysis = dynamic_analyzer.analyze(code)

        questions = template.generate_questions(static_analysis, dynamic_analysis)

        # Should have questions from both global and function scope
        assert len(questions) > 0

        # Check that scope information is captured
        for question in questions:
            assert question.context['scope'] in ['global', 'calculate']


class TestLoopIterationCountTemplate:
    """Tests for LoopIterationCountTemplate."""

    def test_is_applicable_with_loops(self):
        """Template should be applicable when code has loops and executes."""
        template = LoopIterationCountTemplate()
        static_analysis = {
            'loops': [
                {'type': 'for', 'line_start': 1}
            ]
        }
        dynamic_analysis = {
            'execution_successful': True
        }
        assert template.is_applicable(static_analysis, dynamic_analysis) is True

    def test_is_not_applicable_without_loops(self):
        """Template should not be applicable without loops."""
        template = LoopIterationCountTemplate()
        static_analysis = {'loops': []}
        dynamic_analysis = {'execution_successful': True}
        assert template.is_applicable(static_analysis, dynamic_analysis) is False

    def test_is_not_applicable_without_execution(self):
        """Template should not be applicable without dynamic analysis."""
        template = LoopIterationCountTemplate()
        static_analysis = {
            'loops': [{'type': 'for', 'line_start': 1}]
        }
        assert template.is_applicable(static_analysis, None) is False

    def test_generate_question_for_loop(self):
        """Should generate question about for loop iterations."""
        template = LoopIterationCountTemplate()

        code = """
total = 0
for i in range(5):
    total += i
"""
        static_analyzer = StaticAnalyzer()
        dynamic_analyzer = DynamicAnalyzer()

        static_analysis = static_analyzer.analyze(code)
        dynamic_analysis = dynamic_analyzer.analyze(code)

        questions = template.generate_questions(static_analysis, dynamic_analysis)

        assert len(questions) == 1
        question = questions[0]

        assert question.template_id == 'loop_iteration_count'
        assert 'loop' in question.question_text.lower()
        assert 'iterate' in question.question_text.lower() or 'times' in question.question_text.lower()
        assert question.question_type == QuestionType.NUMERIC
        assert question.correct_answer == 5
        assert question.context['loop_type'] == 'for'

    def test_generate_question_while_loop(self):
        """Should generate question about while loop iterations."""
        template = LoopIterationCountTemplate()

        code = """
count = 0
while count < 3:
    count += 1
"""
        static_analyzer = StaticAnalyzer()
        dynamic_analyzer = DynamicAnalyzer()

        static_analysis = static_analyzer.analyze(code)
        dynamic_analysis = dynamic_analyzer.analyze(code)

        questions = template.generate_questions(static_analysis, dynamic_analysis)

        assert len(questions) == 1
        question = questions[0]

        assert question.correct_answer == 3
        assert question.context['loop_type'] == 'while'

    def test_generate_question_nested_loops(self):
        """Should generate questions for nested loops."""
        template = LoopIterationCountTemplate()

        code = """
for i in range(3):
    for j in range(2):
        pass
"""
        static_analyzer = StaticAnalyzer()
        dynamic_analyzer = DynamicAnalyzer()

        static_analysis = static_analyzer.analyze(code)
        dynamic_analysis = dynamic_analyzer.analyze(code)

        questions = template.generate_questions(static_analysis, dynamic_analysis)

        # Should have questions for both loops
        assert len(questions) == 2

        # Outer loop should have 3 iterations
        # Inner loop will be visited multiple times due to nesting
        iteration_counts = [q.correct_answer for q in questions]
        assert 3 in iteration_counts
        # Inner loop count will be higher due to how settrace counts revisits
        assert all(count > 0 for count in iteration_counts)


class TestTemplateRegistry:
    """Tests for TemplateRegistry."""

    def test_registry_initialization(self):
        """Registry should initialize with default templates."""
        registry = TemplateRegistry()

        assert len(registry.templates) == 3
        template_ids = [t.template_id for t in registry.templates]

        assert 'recursive_function_detection' in template_ids
        assert 'variable_value_tracing' in template_ids
        assert 'loop_iteration_count' in template_ids

    def test_register_new_template(self):
        """Should be able to register new templates."""
        registry = TemplateRegistry()
        initial_count = len(registry.templates)

        # Create a dummy template
        class DummyTemplate(QuestionTemplate):
            def __init__(self):
                super().__init__(
                    template_id='dummy',
                    name='Dummy',
                    description='Test',
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    question_level=QuestionLevel.ATOM,
                    answer_type=AnswerType.STATIC
                )

            def is_applicable(self, static_analysis, dynamic_analysis=None):
                return True

            def generate_questions(self, static_analysis, dynamic_analysis=None, source_code=None):
                return []

        registry.register(DummyTemplate())
        assert len(registry.templates) == initial_count + 1

    def test_get_applicable_templates(self):
        """Should find applicable templates based on analysis."""
        registry = TemplateRegistry()

        # Code with functions but no loops
        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def helper(x):
    return x
"""
        static_analyzer = StaticAnalyzer()
        static_analysis = static_analyzer.analyze(code)

        applicable = registry.get_applicable_templates(static_analysis)

        # Should have recursive function template
        template_ids = [t.template_id for t in applicable]
        assert 'recursive_function_detection' in template_ids

        # Should not have loop iteration template
        assert 'loop_iteration_count' not in template_ids

    def test_get_applicable_templates_with_execution(self):
        """Should find templates requiring dynamic analysis."""
        registry = TemplateRegistry()

        code = """
x = 5
for i in range(3):
    x += i
"""
        static_analyzer = StaticAnalyzer()
        dynamic_analyzer = DynamicAnalyzer()

        static_analysis = static_analyzer.analyze(code)
        dynamic_analysis = dynamic_analyzer.analyze(code)

        applicable = registry.get_applicable_templates(static_analysis, dynamic_analysis)

        template_ids = [t.template_id for t in applicable]

        # Should have both variable and loop templates
        assert 'variable_value_tracing' in template_ids
        assert 'loop_iteration_count' in template_ids

    def test_get_template_by_id(self):
        """Should retrieve template by ID."""
        registry = TemplateRegistry()

        template = registry.get_template_by_id('recursive_function_detection')
        assert template is not None
        assert isinstance(template, RecursiveFunctionTemplate)

        template = registry.get_template_by_id('nonexistent')
        assert template is None

    def test_list_templates(self):
        """Should list all templates with metadata."""
        registry = TemplateRegistry()

        templates = registry.list_templates()

        assert len(templates) == 3
        assert all('id' in t for t in templates)
        assert all('name' in t for t in templates)
        assert all('description' in t for t in templates)

    def test_global_registry_singleton(self):
        """get_registry() should return the same instance."""
        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2


class TestGeneratedQuestion:
    """Tests for GeneratedQuestion data structure."""

    def test_to_dict_serialization(self):
        """Should serialize to dictionary correctly."""
        from question_engine.templates import GeneratedQuestion, QuestionAnswer

        question = GeneratedQuestion(
            template_id='test_template',
            question_text='What is the answer?',
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_level=QuestionLevel.ATOM,
            answer_type=AnswerType.STATIC,
            correct_answer='42',
            answer_choices=[
                QuestionAnswer(text='42', is_correct=True),
                QuestionAnswer(text='24', is_correct=False)
            ],
            context={'key': 'value'},
            difficulty='easy'
        )

        result = question.to_dict()

        assert result['template_id'] == 'test_template'
        assert result['question_text'] == 'What is the answer?'
        assert result['question_type'] == 'multiple_choice'
        assert result['question_level'] == 'atom'
        assert result['correct_answer'] == '42'
        assert len(result['answer_choices']) == 2
        assert result['context'] == {'key': 'value'}
        assert result['difficulty'] == 'easy'


class TestIntegration:
    """Integration tests with real code analysis."""

    def test_full_workflow_simple_program(self):
        """Test complete workflow from code to questions."""
        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def double(x):
    return x * 2

result = factorial(5)
value = double(10)
"""
        # Analyze code
        static_analyzer = StaticAnalyzer()
        dynamic_analyzer = DynamicAnalyzer()

        static_analysis = static_analyzer.analyze(code)
        dynamic_analysis = dynamic_analyzer.analyze(code)

        # Get applicable templates
        registry = get_registry()
        applicable = registry.get_applicable_templates(static_analysis, dynamic_analysis)

        # Should have multiple applicable templates
        assert len(applicable) > 0

        # Generate questions
        all_questions = []
        for template in applicable:
            questions = template.generate_questions(static_analysis, dynamic_analysis, code)
            all_questions.extend(questions)

        # Should generate multiple questions
        assert len(all_questions) > 0

        # Each question should be complete
        for question in all_questions:
            assert question.question_text != ''
            assert question.template_id != ''
            assert question.question_type is not None

            # Should be serializable
            question_dict = question.to_dict()
            assert isinstance(question_dict, dict)
