"""
Question Generator

Orchestrates the complete question generation pipeline:
1. Analyzes student code (static + dynamic)
2. Finds applicable question templates
3. Generates questions from templates
4. Filters and prioritizes questions
5. Returns final set of questions

This is the main entry point for the QLC system.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import sys
from pathlib import Path

# Import analyzers
sys.path.insert(0, str(Path(__file__).parent.parent))
from analyzers.static_analyzer import StaticAnalyzer
from analyzers.dynamic_analyzer import DynamicAnalyzer
from question_engine.templates import (
    get_registry,
    TemplateRegistry,
    GeneratedQuestion,
    QuestionLevel,
    QuestionType
)


class GenerationStrategy(Enum):
    """Strategy for selecting questions."""
    ALL = "all"                      # Return all generated questions
    DIVERSE = "diverse"              # Maximize diversity across levels and types
    FOCUSED = "focused"              # Focus on specific areas
    ADAPTIVE = "adaptive"            # Adapt based on code complexity


@dataclass
class GenerationConfig:
    """Configuration for question generation."""

    # Analysis settings
    enable_static_analysis: bool = True
    enable_dynamic_analysis: bool = True
    dynamic_timeout: int = 5  # seconds

    # Question selection
    strategy: GenerationStrategy = GenerationStrategy.DIVERSE
    max_questions: Optional[int] = 10
    min_questions: Optional[int] = 3

    # Filtering
    allowed_levels: Set[QuestionLevel] = field(default_factory=lambda: {
        QuestionLevel.ATOM,
        QuestionLevel.BLOCK,
        QuestionLevel.RELATIONAL,
        QuestionLevel.MACRO
    })
    allowed_types: Set[QuestionType] = field(default_factory=lambda: {
        QuestionType.MULTIPLE_CHOICE,
        QuestionType.FILL_IN_BLANK,
        QuestionType.NUMERIC,
        QuestionType.TRUE_FALSE,
        QuestionType.SHORT_ANSWER,
        QuestionType.CODE_SELECTION
    })
    allowed_difficulties: Set[str] = field(default_factory=lambda: {"easy", "medium", "hard"})

    # Deduplication
    remove_similar_questions: bool = True
    similarity_threshold: float = 0.8

    # Prioritization
    prefer_levels: List[QuestionLevel] = field(default_factory=list)
    prefer_types: List[QuestionType] = field(default_factory=list)


@dataclass
class GenerationResult:
    """Result of question generation process."""

    questions: List[GeneratedQuestion]

    # Analysis results (for debugging/logging)
    static_analysis: Optional[Dict[str, Any]] = None
    dynamic_analysis: Optional[Dict[str, Any]] = None

    # Metadata
    total_generated: int = 0
    total_filtered: int = 0
    applicable_templates: int = 0

    # Errors/warnings
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Execution info
    execution_successful: bool = True
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'questions': [q.to_dict() for q in self.questions],
            'metadata': {
                'total_generated': self.total_generated,
                'total_filtered': self.total_filtered,
                'total_returned': len(self.questions),
                'applicable_templates': self.applicable_templates,
                'execution_successful': self.execution_successful,
                'execution_time_ms': self.execution_time_ms
            },
            'errors': self.errors,
            'warnings': self.warnings,
            'static_analysis_summary': self._summarize_static() if self.static_analysis else None,
            'dynamic_analysis_summary': self._summarize_dynamic() if self.dynamic_analysis else None
        }

    def _summarize_static(self) -> Dict[str, Any]:
        """Create a summary of static analysis."""
        if not self.static_analysis:
            return {}
        return self.static_analysis.get('summary', {})

    def _summarize_dynamic(self) -> Dict[str, Any]:
        """Create a summary of dynamic analysis."""
        if not self.dynamic_analysis:
            return {}
        return {
            'execution_successful': self.dynamic_analysis.get('execution_successful', False),
            'max_stack_depth': self.dynamic_analysis.get('max_stack_depth', 0),
            'total_lines_executed': self.dynamic_analysis.get('total_lines_executed', 0),
            'exception': self.dynamic_analysis.get('exception')
        }


class QuestionGenerator:
    """
    Main question generator class.
    Orchestrates the entire question generation pipeline.
    """

    def __init__(self, config: Optional[GenerationConfig] = None):
        """
        Initialize the question generator.

        Args:
            config: Configuration for question generation
        """
        self.config = config or GenerationConfig()
        self.static_analyzer = StaticAnalyzer()
        self.dynamic_analyzer = DynamicAnalyzer(timeout=self.config.dynamic_timeout)
        self.template_registry = get_registry()

    def generate(
        self,
        source_code: str,
        test_inputs: Optional[Dict[str, Any]] = None
    ) -> GenerationResult:
        """
        Generate questions from student code.

        Args:
            source_code: Python source code to analyze
            test_inputs: Optional inputs for dynamic analysis

        Returns:
            GenerationResult with questions and metadata
        """
        import time
        start_time = time.time()

        result = GenerationResult(questions=[])

        # Step 1: Static Analysis
        static_analysis = None
        if self.config.enable_static_analysis:
            try:
                static_analysis = self.static_analyzer.analyze(source_code)
                result.static_analysis = static_analysis
            except SyntaxError as e:
                result.errors.append(f"Syntax error in code: {e}")
                result.execution_successful = False
                return result
            except Exception as e:
                result.errors.append(f"Static analysis failed: {e}")
                result.warnings.append("Continuing without static analysis")

        # Step 2: Dynamic Analysis
        dynamic_analysis = None
        if self.config.enable_dynamic_analysis:
            try:
                dynamic_analysis = self.dynamic_analyzer.analyze(source_code, test_inputs)
                result.dynamic_analysis = dynamic_analysis
                result.execution_successful = dynamic_analysis.get('execution_successful', False)

                if not result.execution_successful:
                    exception = dynamic_analysis.get('exception', 'Unknown error')
                    result.warnings.append(f"Code execution failed: {exception}")
                    result.warnings.append("Questions will be limited to static analysis only")
            except Exception as e:
                result.errors.append(f"Dynamic analysis failed: {e}")
                result.warnings.append("Continuing without dynamic analysis")

        # If both analyses failed, return early
        if not static_analysis and not dynamic_analysis:
            result.errors.append("Both static and dynamic analysis failed")
            return result

        # Step 3: Find applicable templates
        applicable_templates = self.template_registry.get_applicable_templates(
            static_analysis or {},
            dynamic_analysis
        )
        result.applicable_templates = len(applicable_templates)

        if not applicable_templates:
            result.warnings.append("No applicable question templates found for this code")
            return result

        # Step 4: Generate questions from templates
        all_questions = []
        for template in applicable_templates:
            try:
                questions = template.generate_questions(
                    static_analysis or {},
                    dynamic_analysis,
                    source_code
                )
                all_questions.extend(questions)
            except Exception as e:
                result.warnings.append(f"Template {template.template_id} failed: {e}")

        result.total_generated = len(all_questions)

        # Step 5: Filter questions
        filtered_questions = self._filter_questions(all_questions)

        # Step 6: Remove duplicates/similar questions
        if self.config.remove_similar_questions:
            filtered_questions = self._deduplicate_questions(filtered_questions)

        # Step 7: Prioritize and select final set
        final_questions = self._select_questions(filtered_questions)

        result.questions = final_questions
        result.total_filtered = result.total_generated - len(final_questions)

        # Calculate execution time
        end_time = time.time()
        result.execution_time_ms = (end_time - start_time) * 1000

        return result

    def _filter_questions(self, questions: List[GeneratedQuestion]) -> List[GeneratedQuestion]:
        """
        Filter questions based on configuration.

        Args:
            questions: List of questions to filter

        Returns:
            Filtered list of questions
        """
        filtered = []

        for question in questions:
            # Check level
            if question.question_level not in self.config.allowed_levels:
                continue

            # Check type
            if question.question_type not in self.config.allowed_types:
                continue

            # Check difficulty
            if question.difficulty not in self.config.allowed_difficulties:
                continue

            filtered.append(question)

        return filtered

    def _deduplicate_questions(self, questions: List[GeneratedQuestion]) -> List[GeneratedQuestion]:
        """
        Remove duplicate or very similar questions.

        Args:
            questions: List of questions to deduplicate

        Returns:
            Deduplicated list of questions
        """
        if not questions:
            return []

        # Group by template ID (questions from same template are similar)
        from collections import defaultdict
        by_template = defaultdict(list)

        for question in questions:
            by_template[question.template_id].append(question)

        # For each template, keep diverse questions
        deduplicated = []

        for template_id, template_questions in by_template.items():
            # For variable value questions, limit to 2-3 most interesting ones
            if template_id == 'variable_value_tracing':
                # Filter out function definitions if there are other variables
                non_function_vars = [q for q in template_questions
                                    if q.context.get('value_type') != 'function']

                if non_function_vars:
                    # Prefer non-function variables
                    selected = non_function_vars[:3]
                else:
                    # Keep some function variables if that's all we have
                    selected = template_questions[:2]

                deduplicated.extend(selected)
            else:
                # For other templates, keep all questions
                deduplicated.extend(template_questions)

        return deduplicated

    def _select_questions(self, questions: List[GeneratedQuestion]) -> List[GeneratedQuestion]:
        """
        Select final set of questions based on strategy.

        Args:
            questions: List of filtered questions

        Returns:
            Final selected questions
        """
        if not questions:
            return []

        # Apply max limit
        if self.config.max_questions and len(questions) > self.config.max_questions:
            questions = self._prioritize_questions(questions)[:self.config.max_questions]

        # Check min limit
        if self.config.min_questions and len(questions) < self.config.min_questions:
            # Could generate warning, but we'll just return what we have
            pass

        return questions

    def _prioritize_questions(self, questions: List[GeneratedQuestion]) -> List[GeneratedQuestion]:
        """
        Prioritize questions based on configuration and strategy.

        Args:
            questions: List of questions to prioritize

        Returns:
            Prioritized list of questions
        """
        if self.config.strategy == GenerationStrategy.ALL:
            return questions

        elif self.config.strategy == GenerationStrategy.DIVERSE:
            # Maximize diversity across levels and types
            return self._diverse_selection(questions)

        elif self.config.strategy == GenerationStrategy.FOCUSED:
            # Prioritize based on preferences
            return self._focused_selection(questions)

        elif self.config.strategy == GenerationStrategy.ADAPTIVE:
            # Adapt based on code complexity
            return self._adaptive_selection(questions)

        return questions

    def _diverse_selection(self, questions: List[GeneratedQuestion]) -> List[GeneratedQuestion]:
        """Select questions to maximize diversity."""
        # Group by level and type
        from collections import defaultdict
        by_level = defaultdict(list)

        for question in questions:
            key = (question.question_level, question.question_type)
            by_level[key].append(question)

        # Round-robin selection to ensure diversity
        selected = []
        keys = list(by_level.keys())

        while by_level and (not self.config.max_questions or len(selected) < self.config.max_questions):
            for key in keys:
                if key in by_level and by_level[key]:
                    selected.append(by_level[key].pop(0))
                    if not by_level[key]:
                        del by_level[key]

                    if self.config.max_questions and len(selected) >= self.config.max_questions:
                        break

        return selected

    def _focused_selection(self, questions: List[GeneratedQuestion]) -> List[GeneratedQuestion]:
        """Select questions based on preferences."""
        def priority_score(question: GeneratedQuestion) -> Tuple[int, int]:
            level_priority = 0
            if self.config.prefer_levels and question.question_level in self.config.prefer_levels:
                level_priority = len(self.config.prefer_levels) - self.config.prefer_levels.index(question.question_level)

            type_priority = 0
            if self.config.prefer_types and question.question_type in self.config.prefer_types:
                type_priority = len(self.config.prefer_types) - self.config.prefer_types.index(question.question_type)

            return (level_priority, type_priority)

        # Sort by priority (higher is better)
        sorted_questions = sorted(questions, key=priority_score, reverse=True)
        return sorted_questions

    def _adaptive_selection(self, questions: List[GeneratedQuestion]) -> List[GeneratedQuestion]:
        """Adapt selection based on code complexity."""
        # For now, use diverse selection
        # In future, could analyze code complexity and adjust accordingly
        return self._diverse_selection(questions)


# Convenience functions

def generate_questions(
    source_code: str,
    config: Optional[GenerationConfig] = None,
    test_inputs: Optional[Dict[str, Any]] = None
) -> GenerationResult:
    """
    Convenience function to generate questions from code.

    Args:
        source_code: Python source code
        config: Optional generation configuration
        test_inputs: Optional inputs for dynamic analysis

    Returns:
        GenerationResult with questions and metadata
    """
    generator = QuestionGenerator(config)
    return generator.generate(source_code, test_inputs)


def generate_questions_simple(source_code: str, max_questions: int = 10) -> List[GeneratedQuestion]:
    """
    Simplest interface - just get questions.

    Args:
        source_code: Python source code
        max_questions: Maximum number of questions to return

    Returns:
        List of generated questions
    """
    config = GenerationConfig(max_questions=max_questions)
    result = generate_questions(source_code, config)
    return result.questions
