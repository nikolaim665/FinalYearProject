"""
API Models (Pydantic Schemas)

Defines request/response models for the REST API.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


# Enums for API
class QuestionLevelEnum(str, Enum):
    """Question difficulty level."""
    ATOM = "atom"
    BLOCK = "block"
    RELATIONAL = "relational"
    MACRO = "macro"


class QuestionTypeEnum(str, Enum):
    """Type of question."""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    NUMERIC = "numeric"
    CODE_SELECTION = "code_selection"


class StrategyEnum(str, Enum):
    """Question selection strategy."""
    ALL = "all"
    DIVERSE = "diverse"
    FOCUSED = "focused"
    ADAPTIVE = "adaptive"


# Request Models

class CodeSubmissionRequest(BaseModel):
    """Request model for code submission."""
    code: str = Field(
        ...,
        description="Python source code to analyze",
        min_length=1,
        max_length=50000
    )
    test_inputs: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional test inputs for dynamic analysis"
    )
    max_questions: Optional[int] = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of questions to generate"
    )
    strategy: Optional[StrategyEnum] = Field(
        default=StrategyEnum.DIVERSE,
        description="Question selection strategy"
    )
    allowed_levels: Optional[List[QuestionLevelEnum]] = Field(
        default=None,
        description="Filter questions by level"
    )
    allowed_types: Optional[List[QuestionTypeEnum]] = Field(
        default=None,
        description="Filter questions by type"
    )
    allowed_difficulties: Optional[List[str]] = Field(
        default=None,
        description="Filter questions by difficulty (easy, medium, hard)"
    )

    @field_validator('code')
    @classmethod
    def code_not_empty(cls, v: str) -> str:
        """Validate code is not just whitespace."""
        if not v.strip():
            raise ValueError('Code cannot be empty or only whitespace')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "code": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n\nresult = factorial(5)",
                "max_questions": 5,
                "strategy": "diverse"
            }
        }


class AnswerSubmissionRequest(BaseModel):
    """Request model for submitting an answer."""
    submission_id: str = Field(..., description="ID of the code submission")
    question_id: str = Field(..., description="ID of the question")
    answer: Any = Field(..., description="Student's answer")

    class Config:
        json_schema_extra = {
            "example": {
                "submission_id": "sub_123",
                "question_id": "q_456",
                "answer": "factorial"
            }
        }


# Response Models

class AnswerChoice(BaseModel):
    """A single answer choice for multiple choice questions."""
    text: str
    is_correct: bool
    explanation: Optional[str] = None


class WrongAnswerExplanation(BaseModel):
    """Explanation of why a wrong answer choice is wrong."""
    answer_text: str
    explanation: str
    common_misconception: Optional[str] = None


class AnswerExplanationDetail(BaseModel):
    """Rich explanation from the answer explainer LLM."""
    verified_correct_answer: Optional[Any] = None
    is_answer_verified: bool = True
    correct_answer_reasoning: str = ""
    code_references: List[str] = Field(
        default=[],
        description="References to specific lines of code"
    )
    analysis_references: List[str] = Field(
        default=[],
        description="References to static/dynamic analysis data"
    )
    wrong_answer_explanations: List[WrongAnswerExplanation] = Field(
        default=[],
        description="Explanations of why each wrong answer is wrong"
    )
    learning_tip: Optional[str] = None
    corrected_answer: Optional[Any] = None


class Question(BaseModel):
    """A generated question."""
    id: str = Field(description="Unique question identifier")
    template_id: str
    question_text: str
    question_type: QuestionTypeEnum
    question_level: QuestionLevelEnum
    answer_type: str
    correct_answer: Any
    alternative_answers: List[str] = Field(
        default=[],
        description="Alternative acceptable answers for numeric questions"
    )
    answer_choices: List[AnswerChoice] = []
    context: Dict[str, Any] = {}
    explanation: Optional[str] = None
    difficulty: str = "medium"
    answer_explanation: Optional[AnswerExplanationDetail] = Field(
        default=None,
        description="Rich explanation from the answer explainer LLM with verification, code references, and wrong answer explanations"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "q_123",
                "template_id": "recursive_function_detection",
                "question_text": "What type of function is factorial?",
                "question_type": "multiple_choice",
                "question_level": "block",
                "answer_type": "static",
                "correct_answer": "recursive",
                "alternative_answers": [],
                "answer_choices": [],
                "difficulty": "medium"
            }
        }


class AnalysisSummary(BaseModel):
    """Summary of code analysis."""
    total_functions: Optional[int] = 0
    total_variables: Optional[int] = 0
    total_loops: Optional[int] = 0
    total_conditionals: Optional[int] = 0
    has_recursion: Optional[bool] = False
    execution_successful: Optional[bool] = None
    max_stack_depth: Optional[int] = None


class GenerationMetadata(BaseModel):
    """Metadata about question generation."""
    total_generated: int
    total_filtered: int
    total_returned: int
    applicable_templates: int
    execution_successful: bool
    execution_time_ms: float


class CodeSubmissionResponse(BaseModel):
    """Response model for code submission."""
    submission_id: str = Field(description="Unique submission identifier")
    questions: List[Question]
    metadata: GenerationMetadata
    analysis_summary: AnalysisSummary
    errors: List[str] = []
    warnings: List[str] = []

    class Config:
        json_schema_extra = {
            "example": {
                "submission_id": "sub_abc123",
                "questions": [
                    {
                        "id": "q_xyz789",
                        "template_id": "recursive_function_detection",
                        "question_text": "Which of the following functions are recursive (call themselves directly or indirectly)?",
                        "question_type": "multiple_choice",
                        "question_level": "block",
                        "answer_type": "static",
                        "correct_answer": "factorial",
                        "answer_choices": [
                            {
                                "text": "factorial",
                                "is_correct": True,
                                "explanation": "Calls itself"
                            },
                            {
                                "text": "helper",
                                "is_correct": False,
                                "explanation": "Does not call itself"
                            }
                        ],
                        "context": {
                            "total_functions": 2,
                            "recursive_count": 1,
                            "function_names": ["factorial", "helper"]
                        },
                        "explanation": "The factorial function calls itself on line 4",
                        "difficulty": "medium"
                    }
                ],
                "metadata": {
                    "total_generated": 8,
                    "total_filtered": 3,
                    "total_returned": 5,
                    "applicable_templates": 3,
                    "execution_successful": True,
                    "execution_time_ms": 12.5
                },
                "analysis_summary": {
                    "total_functions": 2,
                    "has_recursion": True
                },
                "errors": [],
                "warnings": []
            }
        }


class AnswerFeedback(BaseModel):
    """Feedback on a submitted answer."""
    is_correct: bool
    explanation: str
    correct_answer: Optional[Any] = None


class AnswerSubmissionResponse(BaseModel):
    """Response model for answer submission."""
    submission_id: str
    question_id: str
    feedback: AnswerFeedback

    class Config:
        json_schema_extra = {
            "example": {
                "submission_id": "sub_123",
                "question_id": "q_456",
                "feedback": {
                    "is_correct": True,
                    "explanation": "Correct! The factorial function calls itself recursively."
                }
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    components: Dict[str, str] = {}

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "components": {
                    "static_analyzer": "ok",
                    "dynamic_analyzer": "ok",
                    "template_system": "ok"
                }
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    status_code: int

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid code",
                "detail": "Syntax error on line 5",
                "status_code": 400
            }
        }


# --- LLM Judge Evaluation Models ---

class QuestionEvaluationResponse(BaseModel):
    """Evaluation of a single question by the LLM judge."""
    question_id: str
    question_text: str
    scores: Dict[str, int] = Field(
        description="Per-dimension scores (1-5): accuracy, clarity, pedagogical_value, code_specificity, difficulty_calibration"
    )
    overall_score: float = Field(description="Weighted overall score (accuracy and pedagogical_value count 2x)")
    explanation: str = Field(description="Judge's reasoning paragraph")
    issues: List[str] = Field(default=[], description="Plain-English problems identified (empty if none)")
    is_flagged: bool = Field(description="True if overall < 3.0 or accuracy < 3")

    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "q_abc123",
                "question_text": "What is the return value of factorial(5)?",
                "scores": {
                    "accuracy": 5,
                    "clarity": 4,
                    "pedagogical_value": 4,
                    "code_specificity": 5,
                    "difficulty_calibration": 3
                },
                "overall_score": 4.43,
                "explanation": "The correct answer (120) is verified by dynamic analysis...",
                "issues": [],
                "is_flagged": False
            }
        }


class EvaluationResultResponse(BaseModel):
    """Complete evaluation of all questions in a submission."""
    submission_id: str
    question_evaluations: List[QuestionEvaluationResponse]
    aggregate: Dict[str, Any] = Field(
        description="Aggregate stats: mean scores per dimension, total questions, flagged count"
    )
    tokens_used: int
    evaluation_time_ms: float

    class Config:
        json_schema_extra = {
            "example": {
                "submission_id": "sub_abc123",
                "question_evaluations": [],
                "aggregate": {
                    "mean_overall": 3.8,
                    "mean_accuracy": 4.1,
                    "mean_clarity": 3.9,
                    "mean_pedagogical_value": 3.6,
                    "mean_code_specificity": 3.4,
                    "mean_difficulty_calibration": 3.7,
                    "total_questions": 8,
                    "questions_flagged": 2,
                    "questions_flagged_ids": ["q_abc123", "q_def456"]
                },
                "tokens_used": 4200,
                "evaluation_time_ms": 8500.0
            }
        }
