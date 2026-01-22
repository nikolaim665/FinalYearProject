"""
Answer Validator for Open-Ended Questions

Provides semantic answer validation that supports multiple correct answers
and intelligent comparison for open-ended questions (short_answer, fill_in_blank).
Also supports numeric validation with tolerance, ranges, and alternative values.
"""

import re
import math
from typing import List, Optional, Tuple, Any, Union, Dict
from dataclasses import dataclass, field
from enum import Enum


class MatchType(Enum):
    """Type of match found during validation."""
    EXACT = "exact"  # Exact string match
    NORMALIZED = "normalized"  # Match after normalization
    ALTERNATIVE = "alternative"  # Matched an alternative answer
    PARTIAL = "partial"  # Partial/semantic match
    NUMERIC_EXACT = "numeric_exact"  # Exact numeric match
    NUMERIC_TOLERANCE = "numeric_tolerance"  # Match within tolerance
    NUMERIC_RANGE = "numeric_range"  # Match within specified range
    NO_MATCH = "no_match"  # No match found


@dataclass
class NumericConfig:
    """Configuration for numeric answer validation."""
    tolerance: float = 0.0001  # Absolute tolerance for comparison
    relative_tolerance: float = 0.01  # Relative tolerance (1% by default)
    allow_equivalent_expressions: bool = True  # e.g., 2^10 = 1024
    range_min: Optional[float] = None  # Minimum value for range validation
    range_max: Optional[float] = None  # Maximum value for range validation


@dataclass
class ValidationResult:
    """Result of answer validation."""
    is_correct: bool
    match_type: MatchType
    matched_answer: Optional[str] = None  # Which answer it matched (if any)
    confidence: float = 1.0  # Confidence score (1.0 = certain, 0.0 = no confidence)
    feedback: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)  # Additional validation details


class AnswerValidator:
    """
    Validates student answers against correct answers with support for
    multiple acceptable answers and semantic matching.
    """

    # Common stop words to ignore in comparison
    STOP_WORDS = {
        'a', 'an', 'the', 'is', 'are', 'was', 'were', 'it', 'its',
        'to', 'of', 'for', 'in', 'on', 'at', 'by', 'with',
        'this', 'that', 'these', 'those', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall'
    }

    # Comprehensive programming synonyms for semantic matching
    PROGRAMMING_SYNONYMS = {
        # Control flow
        'loop': {'iteration', 'repetition', 'cycle', 'looping', 'iterate', 'repeat'},
        'iteration': {'loop', 'repetition', 'cycle', 'looping', 'iterate'},
        'while': {'while loop', 'loop while', 'repeat while'},
        'for': {'for loop', 'loop for', 'for each', 'foreach'},
        'condition': {'conditional', 'if statement', 'branch', 'check', 'test'},
        'conditional': {'condition', 'if statement', 'branch', 'if-else'},
        'branch': {'condition', 'if', 'decision', 'conditional'},
        'break': {'exit loop', 'stop loop', 'terminate loop'},
        'continue': {'skip iteration', 'next iteration', 'skip'},

        # Functions and methods
        'function': {'method', 'procedure', 'routine', 'subroutine', 'def', 'func'},
        'method': {'function', 'procedure', 'routine', 'member function'},
        'recursive': {'recursion', 'self-calling', 'calls itself', 'recurse'},
        'recursion': {'recursive', 'self-calling', 'calls itself'},
        'parameter': {'argument', 'arg', 'param', 'input'},
        'argument': {'parameter', 'arg', 'param', 'input value'},
        'return': {'returns', 'returned', 'output', 'outputs', 'gives back'},
        'call': {'invoke', 'execute', 'run', 'calling'},

        # Variables and data
        'variable': {'var', 'value', 'identifier', 'name'},
        'assign': {'set', 'store', 'give value', 'assignment'},
        'initialize': {'init', 'create', 'declare', 'set up'},
        'global': {'global variable', 'module-level', 'outer scope'},
        'local': {'local variable', 'function scope', 'inner scope'},

        # Data types
        'list': {'array', 'collection', 'sequence', 'vector'},
        'array': {'list', 'collection', 'sequence', 'vector'},
        'string': {'text', 'str', 'characters', 'char sequence'},
        'integer': {'int', 'number', 'whole number', 'counting number'},
        'float': {'decimal', 'floating point', 'real number', 'double'},
        'boolean': {'bool', 'true/false', 'flag', 'logical'},
        'dictionary': {'dict', 'map', 'hash map', 'mapping', 'hash table'},
        'tuple': {'immutable list', 'fixed sequence', 'pair'},
        'set': {'unique collection', 'distinct values', 'unordered collection'},
        'none': {'null', 'nothing', 'empty', 'nil'},

        # Operations
        'sum': {'total', 'addition', 'aggregate', 'add up'},
        'total': {'sum', 'aggregate', 'cumulative', 'combined'},
        'product': {'multiply', 'multiplication', 'times'},
        'difference': {'subtract', 'minus', 'subtraction'},
        'quotient': {'divide', 'division', 'divided by'},
        'modulo': {'remainder', 'mod', '%'},
        'concatenate': {'join', 'combine', 'merge', 'append strings'},
        'append': {'add', 'push', 'add to end'},
        'prepend': {'add to start', 'add to beginning', 'insert at start'},
        'remove': {'delete', 'pop', 'discard', 'eliminate'},

        # Actions
        'prints': {'outputs', 'displays', 'shows', 'writes', 'logs'},
        'calculates': {'computes', 'determines', 'finds', 'evaluates'},
        'stores': {'holds', 'contains', 'keeps', 'saves'},
        'increments': {'increases', 'adds to', 'adds 1', 'plus 1', '++'},
        'decrements': {'decreases', 'subtracts from', 'subtracts 1', 'minus 1', '--'},
        'iterates': {'loops', 'goes through', 'traverses', 'walks through'},
        'checks': {'tests', 'verifies', 'validates', 'examines'},
        'compares': {'tests equality', 'checks if equal', 'matches'},

        # Concepts
        'algorithm': {'procedure', 'method', 'process', 'steps'},
        'complexity': {'efficiency', 'performance', 'big o'},
        'scope': {'visibility', 'namespace', 'context'},
        'reference': {'pointer', 'address', 'ref'},
        'value': {'data', 'content', 'result'},
        'index': {'position', 'location', 'offset', 'subscript'},
        'element': {'item', 'member', 'entry', 'value'},
        'key': {'identifier', 'name', 'lookup key'},
        'length': {'size', 'count', 'number of elements', 'len'},

        # Errors
        'error': {'exception', 'fault', 'bug', 'problem'},
        'exception': {'error', 'fault', 'runtime error'},
        'syntax error': {'parse error', 'invalid syntax'},
        'runtime error': {'execution error', 'runtime exception'},
    }

    # Numeric equivalents for common values
    NUMERIC_EQUIVALENTS = {
        'pi': 3.14159265358979,
        'e': 2.71828182845905,
        'phi': 1.61803398874989,  # Golden ratio
        'sqrt2': 1.41421356237310,
        'sqrt3': 1.73205080756888,
    }

    def __init__(
        self,
        case_sensitive: bool = False,
        allow_partial: bool = True,
        numeric_config: Optional[NumericConfig] = None
    ):
        """
        Initialize the validator.

        Args:
            case_sensitive: Whether comparisons are case-sensitive
            allow_partial: Whether to allow partial/semantic matching
            numeric_config: Configuration for numeric validation
        """
        self.case_sensitive = case_sensitive
        self.allow_partial = allow_partial
        self.numeric_config = numeric_config or NumericConfig()

    def validate(
        self,
        student_answer: str,
        correct_answer: str,
        alternative_answers: Optional[List[str]] = None,
        question_type: str = "short_answer",
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate a student's answer against correct and alternative answers.

        Args:
            student_answer: The student's submitted answer
            correct_answer: The primary correct answer
            alternative_answers: List of alternative acceptable answers
            question_type: Type of question (affects matching strategy)
            context: Optional context about the question (variable name, function, etc.)

        Returns:
            ValidationResult with match information
        """
        if alternative_answers is None:
            alternative_answers = []
        if context is None:
            context = {}

        # Handle numeric questions separately
        if question_type == "numeric":
            return self._validate_numeric(
                student_answer,
                correct_answer,
                alternative_answers,
                context
            )

        # Normalize the student answer
        normalized_student = self._normalize(student_answer)

        # Check against primary answer first
        primary_result = self._check_answer(normalized_student, correct_answer, is_primary=True)
        if primary_result.is_correct:
            return primary_result

        # Check against alternative answers
        for alt_answer in alternative_answers:
            alt_result = self._check_answer(normalized_student, alt_answer, is_primary=False)
            if alt_result.is_correct:
                alt_result.matched_answer = alt_answer
                return alt_result

        # If partial matching is allowed and we haven't found a match, try semantic matching
        if self.allow_partial and question_type in ["short_answer", "fill_in_blank"]:
            semantic_result = self._semantic_match(
                normalized_student,
                correct_answer,
                alternative_answers,
                context
            )
            if semantic_result.is_correct:
                return semantic_result

        # No match found
        return ValidationResult(
            is_correct=False,
            match_type=MatchType.NO_MATCH,
            feedback=f"The expected answer is: {correct_answer}",
            details={"student_answer": student_answer, "expected": correct_answer}
        )

    def _normalize(self, text: str) -> str:
        """Normalize text for comparison."""
        if not text:
            return ""

        # Convert to lowercase if not case sensitive
        if not self.case_sensitive:
            text = text.lower()

        # Remove extra whitespace
        text = ' '.join(text.split())

        # Remove common punctuation at the end
        text = text.rstrip('.,!?;:')

        return text.strip()

    def _check_answer(self, student_answer: str, correct_answer: str, is_primary: bool) -> ValidationResult:
        """Check if student answer matches a correct answer."""
        normalized_correct = self._normalize(correct_answer)

        # Exact match
        if student_answer == normalized_correct:
            return ValidationResult(
                is_correct=True,
                match_type=MatchType.EXACT if is_primary else MatchType.ALTERNATIVE,
                matched_answer=correct_answer if not is_primary else None,
                confidence=1.0,
                feedback="Correct!"
            )

        # Normalized match (without stop words)
        student_key_words = self._extract_key_words(student_answer)
        correct_key_words = self._extract_key_words(normalized_correct)

        if student_key_words == correct_key_words:
            return ValidationResult(
                is_correct=True,
                match_type=MatchType.NORMALIZED,
                matched_answer=correct_answer if not is_primary else None,
                confidence=0.95,
                feedback="Correct!"
            )

        return ValidationResult(
            is_correct=False,
            match_type=MatchType.NO_MATCH
        )

    def _validate_numeric(
        self,
        student_answer: str,
        correct_answer: str,
        alternative_answers: List[str],
        context: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate a numeric answer with tolerance and alternatives.

        Supports:
        - Exact numeric match
        - Match within absolute tolerance
        - Match within relative tolerance
        - Range validation
        - Alternative numeric values
        - Common numeric expressions (e.g., pi, e, sqrt2)
        """
        # Try to parse the student's answer as a number
        student_value = self._parse_numeric(student_answer)
        if student_value is None:
            return ValidationResult(
                is_correct=False,
                match_type=MatchType.NO_MATCH,
                feedback="Please provide a valid numeric answer",
                details={"error": "invalid_numeric_format", "input": student_answer}
            )

        # Parse the correct answer
        correct_value = self._parse_numeric(correct_answer)
        if correct_value is None:
            # If correct answer isn't numeric, fall back to string comparison
            return ValidationResult(
                is_correct=str(student_value) == str(correct_answer),
                match_type=MatchType.EXACT if str(student_value) == str(correct_answer) else MatchType.NO_MATCH,
                feedback="Correct!" if str(student_value) == str(correct_answer) else f"Expected: {correct_answer}"
            )

        # Check for exact match
        if student_value == correct_value:
            return ValidationResult(
                is_correct=True,
                match_type=MatchType.NUMERIC_EXACT,
                confidence=1.0,
                feedback="Correct!",
                details={"student_value": student_value, "correct_value": correct_value}
            )

        # Check within absolute tolerance
        if abs(student_value - correct_value) <= self.numeric_config.tolerance:
            return ValidationResult(
                is_correct=True,
                match_type=MatchType.NUMERIC_TOLERANCE,
                confidence=0.99,
                feedback="Correct!",
                details={
                    "student_value": student_value,
                    "correct_value": correct_value,
                    "tolerance": self.numeric_config.tolerance
                }
            )

        # Check within relative tolerance (for larger numbers)
        if correct_value != 0:
            relative_error = abs(student_value - correct_value) / abs(correct_value)
            if relative_error <= self.numeric_config.relative_tolerance:
                return ValidationResult(
                    is_correct=True,
                    match_type=MatchType.NUMERIC_TOLERANCE,
                    confidence=0.95,
                    feedback="Correct! (within acceptable precision)",
                    details={
                        "student_value": student_value,
                        "correct_value": correct_value,
                        "relative_error": relative_error
                    }
                )

        # Check if within specified range
        range_min = context.get("range_min", self.numeric_config.range_min)
        range_max = context.get("range_max", self.numeric_config.range_max)
        if range_min is not None and range_max is not None:
            if range_min <= student_value <= range_max:
                return ValidationResult(
                    is_correct=True,
                    match_type=MatchType.NUMERIC_RANGE,
                    confidence=0.9,
                    feedback="Correct! Your answer is within the acceptable range.",
                    details={
                        "student_value": student_value,
                        "range": [range_min, range_max]
                    }
                )

        # Check against alternative numeric answers
        for alt in alternative_answers:
            alt_value = self._parse_numeric(alt)
            if alt_value is not None:
                if abs(student_value - alt_value) <= self.numeric_config.tolerance:
                    return ValidationResult(
                        is_correct=True,
                        match_type=MatchType.ALTERNATIVE,
                        matched_answer=alt,
                        confidence=0.95,
                        feedback="Correct!",
                        details={"matched_alternative": alt_value}
                    )

        # No match
        return ValidationResult(
            is_correct=False,
            match_type=MatchType.NO_MATCH,
            feedback=f"Incorrect. The correct answer is: {correct_value}",
            details={
                "student_value": student_value,
                "correct_value": correct_value,
                "difference": abs(student_value - correct_value)
            }
        )

    def _parse_numeric(self, value: str) -> Optional[float]:
        """
        Parse a string as a numeric value.

        Handles:
        - Standard numbers (integers, floats)
        - Scientific notation
        - Common mathematical constants (pi, e)
        - Simple expressions (2^10, 10**2)
        """
        if value is None:
            return None

        value = str(value).strip().lower()

        # Check for common constants
        if value in self.NUMERIC_EQUIVALENTS:
            return self.NUMERIC_EQUIVALENTS[value]

        # Handle common expressions
        # Power expressions: 2^10 or 2**10
        power_match = re.match(r'^(\d+(?:\.\d+)?)\s*[\^*]{1,2}\s*(\d+(?:\.\d+)?)$', value)
        if power_match:
            base = float(power_match.group(1))
            exp = float(power_match.group(2))
            return base ** exp

        # Try direct float conversion
        try:
            return float(value)
        except (ValueError, TypeError):
            pass

        # Handle percentages
        if value.endswith('%'):
            try:
                return float(value[:-1]) / 100
            except ValueError:
                pass

        # Handle fractions like "1/2"
        fraction_match = re.match(r'^(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)$', value)
        if fraction_match:
            numerator = float(fraction_match.group(1))
            denominator = float(fraction_match.group(2))
            if denominator != 0:
                return numerator / denominator

        return None

    def _extract_key_words(self, text: str) -> set:
        """Extract meaningful words from text, removing stop words."""
        if self.case_sensitive:
            words = set(re.findall(r'\b\w+\b', text))
        else:
            words = set(re.findall(r'\b\w+\b', text.lower()))
        return words - self.STOP_WORDS

    def _semantic_match(
        self,
        student_answer: str,
        correct_answer: str,
        alternative_answers: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Perform semantic matching using synonyms and word overlap.

        This is a more lenient matching that considers:
        - Synonym replacement
        - Word overlap percentage
        - Key concept matching
        - Context-aware validation
        """
        if context is None:
            context = {}

        student_words = self._extract_key_words(student_answer)
        correct_words = self._extract_key_words(self._normalize(correct_answer))

        # Expand correct words with synonyms
        expanded_correct = set(correct_words)
        for word in correct_words:
            if word in self.PROGRAMMING_SYNONYMS:
                expanded_correct.update(self.PROGRAMMING_SYNONYMS[word])

        # Expand student words with synonyms
        expanded_student = set(student_words)
        for word in student_words:
            if word in self.PROGRAMMING_SYNONYMS:
                expanded_student.update(self.PROGRAMMING_SYNONYMS[word])

        # Add context-specific terms to the expected set
        context_terms = self._extract_context_terms(context)
        expanded_correct.update(context_terms)

        # Calculate overlap
        if not expanded_correct:
            return ValidationResult(is_correct=False, match_type=MatchType.NO_MATCH)

        overlap = expanded_student.intersection(expanded_correct)
        overlap_ratio = len(overlap) / len(expanded_correct)

        # Calculate bidirectional similarity for better accuracy
        if expanded_student:
            reverse_ratio = len(overlap) / len(expanded_student)
            # Use harmonic mean of both ratios for balanced similarity
            if overlap_ratio > 0 and reverse_ratio > 0:
                combined_ratio = 2 * (overlap_ratio * reverse_ratio) / (overlap_ratio + reverse_ratio)
            else:
                combined_ratio = overlap_ratio
        else:
            combined_ratio = overlap_ratio

        # If high enough overlap, consider it a match
        if combined_ratio >= 0.6:  # Slightly lower threshold with combined ratio
            return ValidationResult(
                is_correct=True,
                match_type=MatchType.PARTIAL,
                confidence=combined_ratio,
                feedback="Correct! Your answer captures the key concept.",
                details={
                    "overlap_ratio": overlap_ratio,
                    "combined_ratio": combined_ratio,
                    "matched_terms": list(overlap)
                }
            )

        # Also check if any alternative answer has high overlap
        for alt in alternative_answers:
            alt_words = self._extract_key_words(self._normalize(alt))
            expanded_alt = set(alt_words)
            for word in alt_words:
                if word in self.PROGRAMMING_SYNONYMS:
                    expanded_alt.update(self.PROGRAMMING_SYNONYMS[word])

            if expanded_alt:
                alt_overlap = expanded_student.intersection(expanded_alt)
                alt_ratio = len(alt_overlap) / len(expanded_alt)
                if alt_ratio >= 0.6:
                    return ValidationResult(
                        is_correct=True,
                        match_type=MatchType.PARTIAL,
                        matched_answer=alt,
                        confidence=alt_ratio,
                        feedback="Correct! Your answer captures the key concept.",
                        details={"matched_alternative": alt, "overlap_ratio": alt_ratio}
                    )

        return ValidationResult(
            is_correct=False,
            match_type=MatchType.NO_MATCH,
            details={
                "student_terms": list(expanded_student),
                "expected_terms": list(expanded_correct),
                "overlap": list(overlap)
            }
        )

    def _extract_context_terms(self, context: Dict[str, Any]) -> set:
        """
        Extract relevant terms from question context.

        Context can include:
        - variable_name: The variable being asked about
        - function_name: The function being asked about
        - line_number: Relevant line in the code
        - data_type: Expected data type
        """
        terms = set()

        if context.get("variable_name"):
            terms.add(context["variable_name"].lower())

        if context.get("function_name"):
            func_name = context["function_name"].lower()
            terms.add(func_name)
            # Add common function name patterns
            if "factorial" in func_name:
                terms.update(["factorial", "recursion", "recursive", "multiply"])
            elif "sum" in func_name or "add" in func_name:
                terms.update(["sum", "total", "addition", "add"])
            elif "sort" in func_name:
                terms.update(["sort", "order", "arrange"])
            elif "search" in func_name or "find" in func_name:
                terms.update(["search", "find", "locate", "lookup"])

        if context.get("data_type"):
            dtype = context["data_type"].lower()
            terms.add(dtype)
            if dtype in self.PROGRAMMING_SYNONYMS:
                terms.update(self.PROGRAMMING_SYNONYMS[dtype])

        return terms


def validate_answer(
    student_answer: Any,
    correct_answer: Any,
    alternative_answers: Optional[List[str]] = None,
    question_type: str = "short_answer",
    case_sensitive: bool = False,
    context: Optional[Dict[str, Any]] = None,
    numeric_config: Optional[NumericConfig] = None
) -> ValidationResult:
    """
    Convenience function to validate an answer.

    Args:
        student_answer: The student's submitted answer
        correct_answer: The primary correct answer
        alternative_answers: List of alternative acceptable answers
        question_type: Type of question
        case_sensitive: Whether to use case-sensitive matching
        context: Optional context about the question
        numeric_config: Optional configuration for numeric validation

    Returns:
        ValidationResult with match information
    """
    validator = AnswerValidator(
        case_sensitive=case_sensitive,
        numeric_config=numeric_config
    )
    return validator.validate(
        str(student_answer),
        str(correct_answer),
        alternative_answers,
        question_type,
        context
    )


def validate_numeric_answer(
    student_answer: Any,
    correct_answer: Any,
    alternative_answers: Optional[List[str]] = None,
    tolerance: float = 0.0001,
    relative_tolerance: float = 0.01,
    range_min: Optional[float] = None,
    range_max: Optional[float] = None
) -> ValidationResult:
    """
    Convenience function specifically for numeric answer validation.

    Args:
        student_answer: The student's numeric answer
        correct_answer: The correct numeric answer
        alternative_answers: Alternative acceptable numeric values
        tolerance: Absolute tolerance for comparison
        relative_tolerance: Relative tolerance (as decimal, e.g., 0.01 = 1%)
        range_min: Minimum acceptable value (if using range)
        range_max: Maximum acceptable value (if using range)

    Returns:
        ValidationResult with match information
    """
    config = NumericConfig(
        tolerance=tolerance,
        relative_tolerance=relative_tolerance,
        range_min=range_min,
        range_max=range_max
    )
    validator = AnswerValidator(numeric_config=config)
    return validator.validate(
        str(student_answer),
        str(correct_answer),
        alternative_answers,
        question_type="numeric",
        context={"range_min": range_min, "range_max": range_max}
    )
