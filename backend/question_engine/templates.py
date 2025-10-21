"""
Question Template System

Defines templates for generating questions about learners' code.
Each template has:
- Requirements: What must be present in the code for this template to apply
- Question format: How to generate the question
- Answer generation: How to extract the correct answer from analysis results
- Question metadata: Type, difficulty, level (atom/block/relational/macro)
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class QuestionLevel(Enum):
    """Question complexity level based on the Block Model."""
    ATOM = "atom"           # Language elements (variables, operators)
    BLOCK = "block"         # Code sections (loops, functions)
    RELATIONAL = "relational"  # Connections between parts
    MACRO = "macro"         # Whole program understanding


class QuestionType(Enum):
    """Type of question and expected answer format."""
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_IN_BLANK = "fill_in_blank"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    NUMERIC = "numeric"
    CODE_SELECTION = "code_selection"  # Select from code elements


class AnswerType(Enum):
    """How the answer is determined."""
    STATIC = "static"      # From static analysis only
    DYNAMIC = "dynamic"    # From dynamic analysis (execution)
    HYBRID = "hybrid"      # Requires both analyses
    OPENAI = "openai"      # Requires OpenAI assessment


@dataclass
class QuestionAnswer:
    """Represents a possible answer to a question."""
    text: str
    is_correct: bool
    explanation: Optional[str] = None


@dataclass
class GeneratedQuestion:
    """A concrete question generated from a template."""
    template_id: str
    question_text: str
    question_type: QuestionType
    question_level: QuestionLevel
    answer_type: AnswerType

    # Answer data depends on question type
    correct_answer: Any  # For fill-in, numeric, short answer
    answer_choices: List[QuestionAnswer] = field(default_factory=list)  # For multiple choice

    # Metadata
    context: Dict[str, Any] = field(default_factory=dict)  # Line numbers, variable names, etc.
    explanation: Optional[str] = None
    difficulty: str = "medium"  # easy, medium, hard

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'template_id': self.template_id,
            'question_text': self.question_text,
            'question_type': self.question_type.value,
            'question_level': self.question_level.value,
            'answer_type': self.answer_type.value,
            'correct_answer': self.correct_answer,
            'answer_choices': [
                {
                    'text': choice.text,
                    'is_correct': choice.is_correct,
                    'explanation': choice.explanation
                }
                for choice in self.answer_choices
            ],
            'context': self.context,
            'explanation': self.explanation,
            'difficulty': self.difficulty
        }


class QuestionTemplate:
    """
    Base class for question templates.
    Each template knows how to generate questions from analysis results.
    """

    def __init__(
        self,
        template_id: str,
        name: str,
        description: str,
        question_type: QuestionType,
        question_level: QuestionLevel,
        answer_type: AnswerType,
        difficulty: str = "medium"
    ):
        self.template_id = template_id
        self.name = name
        self.description = description
        self.question_type = question_type
        self.question_level = question_level
        self.answer_type = answer_type
        self.difficulty = difficulty

    def is_applicable(self, static_analysis: Dict[str, Any], dynamic_analysis: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if this template can be applied to the given code analysis.

        Args:
            static_analysis: Results from static analyzer
            dynamic_analysis: Optional results from dynamic analyzer

        Returns:
            True if template requirements are met
        """
        raise NotImplementedError("Subclasses must implement is_applicable()")

    def generate_questions(
        self,
        static_analysis: Dict[str, Any],
        dynamic_analysis: Optional[Dict[str, Any]] = None,
        source_code: Optional[str] = None
    ) -> List[GeneratedQuestion]:
        """
        Generate one or more questions from the analysis results.

        Args:
            static_analysis: Results from static analyzer
            dynamic_analysis: Optional results from dynamic analyzer
            source_code: Optional original source code

        Returns:
            List of generated questions
        """
        raise NotImplementedError("Subclasses must implement generate_questions()")


# ============================================================================
# INITIAL TEMPLATE IMPLEMENTATIONS
# ============================================================================


class RecursiveFunctionTemplate(QuestionTemplate):
    """
    Template: Which functions are recursive?
    Requirements: Program contains function definitions
    Answer: Auto-generated from static analysis
    """

    def __init__(self):
        super().__init__(
            template_id="recursive_function_detection",
            name="Recursive Function Detection",
            description="Identify which functions call themselves recursively",
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_level=QuestionLevel.BLOCK,
            answer_type=AnswerType.STATIC,
            difficulty="medium"
        )

    def is_applicable(self, static_analysis: Dict[str, Any], dynamic_analysis: Optional[Dict[str, Any]] = None) -> bool:
        """Applicable if there are 2+ functions defined."""
        functions = static_analysis.get('functions', [])
        return len(functions) >= 2

    def generate_questions(
        self,
        static_analysis: Dict[str, Any],
        dynamic_analysis: Optional[Dict[str, Any]] = None,
        source_code: Optional[str] = None
    ) -> List[GeneratedQuestion]:
        """Generate a multiple-choice question about recursive functions."""
        functions = static_analysis.get('functions', [])

        if len(functions) < 2:
            return []

        # Find recursive and non-recursive functions
        recursive_funcs = [f for f in functions if f['is_recursive']]
        non_recursive_funcs = [f for f in functions if not f['is_recursive']]

        # Generate answer choices
        answer_choices = []
        for func in functions:
            answer_choices.append(QuestionAnswer(
                text=func['name'],
                is_correct=func['is_recursive'],
                explanation=f"{'Calls itself' if func['is_recursive'] else 'Does not call itself'}"
            ))

        # Determine correct answer text
        if not recursive_funcs:
            correct_answer = "None of the functions are recursive"
        elif len(recursive_funcs) == 1:
            correct_answer = recursive_funcs[0]['name']
        else:
            correct_answer = ", ".join([f['name'] for f in recursive_funcs])

        question_text = "Which of the following functions are recursive (call themselves directly or indirectly)?"

        question = GeneratedQuestion(
            template_id=self.template_id,
            question_text=question_text,
            question_type=self.question_type,
            question_level=self.question_level,
            answer_type=self.answer_type,
            correct_answer=correct_answer,
            answer_choices=answer_choices,
            context={
                'total_functions': len(functions),
                'recursive_count': len(recursive_funcs),
                'function_names': [f['name'] for f in functions]
            },
            difficulty=self.difficulty
        )

        return [question]


class VariableValueTemplate(QuestionTemplate):
    """
    Template: What is the value of variable X on line Y?
    Requirements: Program executes successfully with variable assignments
    Answer: Auto-generated from dynamic analysis
    """

    def __init__(self):
        super().__init__(
            template_id="variable_value_tracing",
            name="Variable Value Tracing",
            description="Trace the value of a variable at a specific execution point",
            question_type=QuestionType.FILL_IN_BLANK,
            question_level=QuestionLevel.ATOM,
            answer_type=AnswerType.DYNAMIC,
            difficulty="easy"
        )

    def is_applicable(self, static_analysis: Dict[str, Any], dynamic_analysis: Optional[Dict[str, Any]] = None) -> bool:
        """Applicable if code executed successfully and has variable snapshots."""
        if not dynamic_analysis:
            return False

        execution_successful = dynamic_analysis.get('execution_successful', False)
        variable_snapshots = dynamic_analysis.get('variable_snapshots', [])

        return execution_successful and len(variable_snapshots) > 0

    def generate_questions(
        self,
        static_analysis: Dict[str, Any],
        dynamic_analysis: Optional[Dict[str, Any]] = None,
        source_code: Optional[str] = None
    ) -> List[GeneratedQuestion]:
        """Generate questions about variable values at specific lines."""
        if not dynamic_analysis:
            return []

        variable_snapshots = dynamic_analysis.get('variable_snapshots', [])

        # Filter out final state snapshots (line = -1) and duplicates
        # Select interesting snapshots (not in loops to avoid repetition)
        seen_vars = set()
        interesting_snapshots = []

        for snapshot in variable_snapshots:
            if snapshot['line'] > 0:  # Skip final state
                key = (snapshot['name'], snapshot['scope'], snapshot['line'])
                if key not in seen_vars:
                    seen_vars.add(key)
                    interesting_snapshots.append(snapshot)

        # Limit to 3 most interesting questions
        questions = []
        for snapshot in interesting_snapshots[:3]:
            var_name = snapshot['name']
            var_value = snapshot['value']
            line_no = snapshot['line']
            scope = snapshot['scope']

            # Format scope nicely
            scope_text = f"in function '{scope}'" if scope != 'global' else "in the global scope"

            question_text = f"What is the value of variable `{var_name}` on line {line_no} {scope_text}?"

            question = GeneratedQuestion(
                template_id=self.template_id,
                question_text=question_text,
                question_type=self.question_type,
                question_level=self.question_level,
                answer_type=self.answer_type,
                correct_answer=var_value,
                context={
                    'variable_name': var_name,
                    'line_number': line_no,
                    'scope': scope,
                    'value_type': snapshot['value_type']
                },
                explanation=f"At line {line_no}, `{var_name}` has the value `{var_value}` ({snapshot['value_type']})",
                difficulty=self.difficulty
            )

            questions.append(question)

        return questions


class LoopIterationCountTemplate(QuestionTemplate):
    """
    Template: How many iterations does the loop on line X perform?
    Requirements: Program executes successfully and contains loops
    Answer: Auto-generated from dynamic analysis
    """

    def __init__(self):
        super().__init__(
            template_id="loop_iteration_count",
            name="Loop Iteration Count",
            description="Determine the number of iterations a loop executes",
            question_type=QuestionType.NUMERIC,
            question_level=QuestionLevel.BLOCK,
            answer_type=AnswerType.DYNAMIC,
            difficulty="medium"
        )

    def is_applicable(self, static_analysis: Dict[str, Any], dynamic_analysis: Optional[Dict[str, Any]] = None) -> bool:
        """Applicable if code has loops and executed successfully."""
        if not dynamic_analysis:
            return False

        static_loops = static_analysis.get('loops', [])
        execution_successful = dynamic_analysis.get('execution_successful', False)

        return len(static_loops) > 0 and execution_successful

    def generate_questions(
        self,
        static_analysis: Dict[str, Any],
        dynamic_analysis: Optional[Dict[str, Any]] = None,
        source_code: Optional[str] = None
    ) -> List[GeneratedQuestion]:
        """Generate questions about loop iteration counts."""
        if not dynamic_analysis:
            return []

        loop_executions = dynamic_analysis.get('loop_executions', [])

        questions = []
        for loop in loop_executions:
            line_start = loop['line_start']
            iteration_count = loop['iteration_count']
            loop_type = loop['loop_type']

            question_text = f"How many times does the {loop_type} loop starting on line {line_start} iterate?"

            question = GeneratedQuestion(
                template_id=self.template_id,
                question_text=question_text,
                question_type=self.question_type,
                question_level=self.question_level,
                answer_type=self.answer_type,
                correct_answer=iteration_count,
                context={
                    'line_start': line_start,
                    'loop_type': loop_type
                },
                explanation=f"The {loop_type} loop on line {line_start} executes {iteration_count} iteration(s)",
                difficulty=self.difficulty
            )

            questions.append(question)

        return questions


# ============================================================================
# TEMPLATE REGISTRY
# ============================================================================


class TemplateRegistry:
    """
    Central registry for all question templates.
    Manages template discovery and application.
    """

    def __init__(self):
        self.templates: List[QuestionTemplate] = []
        self._register_default_templates()

    def _register_default_templates(self):
        """Register the initial set of templates."""
        self.register(RecursiveFunctionTemplate())
        self.register(VariableValueTemplate())
        self.register(LoopIterationCountTemplate())

    def register(self, template: QuestionTemplate):
        """Register a new template."""
        self.templates.append(template)

    def get_applicable_templates(
        self,
        static_analysis: Dict[str, Any],
        dynamic_analysis: Optional[Dict[str, Any]] = None
    ) -> List[QuestionTemplate]:
        """
        Find all templates applicable to the given analysis results.

        Args:
            static_analysis: Results from static analyzer
            dynamic_analysis: Optional results from dynamic analyzer

        Returns:
            List of applicable templates
        """
        applicable = []

        for template in self.templates:
            try:
                if template.is_applicable(static_analysis, dynamic_analysis):
                    applicable.append(template)
            except Exception as e:
                # Log error but continue checking other templates
                print(f"Error checking template {template.template_id}: {e}")
                continue

        return applicable

    def get_template_by_id(self, template_id: str) -> Optional[QuestionTemplate]:
        """Get a specific template by its ID."""
        for template in self.templates:
            if template.template_id == template_id:
                return template
        return None

    def list_templates(self) -> List[Dict[str, str]]:
        """List all registered templates with metadata."""
        return [
            {
                'id': t.template_id,
                'name': t.name,
                'description': t.description,
                'type': t.question_type.value,
                'level': t.question_level.value,
                'difficulty': t.difficulty
            }
            for t in self.templates
        ]


# Convenience function to get the global registry
_global_registry = None

def get_registry() -> TemplateRegistry:
    """Get the global template registry (singleton pattern)."""
    global _global_registry
    if _global_registry is None:
        _global_registry = TemplateRegistry()
    return _global_registry
