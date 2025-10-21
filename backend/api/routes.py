"""
API Routes

Defines all REST API endpoints for the QLC system.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict
import uuid
import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from api.models import (
    CodeSubmissionRequest,
    CodeSubmissionResponse,
    AnswerSubmissionRequest,
    AnswerSubmissionResponse,
    HealthResponse,
    Question,
    AnswerChoice,
    GenerationMetadata,
    AnalysisSummary,
    AnswerFeedback,
    QuestionLevelEnum,
    QuestionTypeEnum,
    StrategyEnum
)
from question_engine.generator import (
    QuestionGenerator,
    GenerationConfig,
    GenerationStrategy
)
from question_engine.templates import QuestionLevel, QuestionType

# Create router
router = APIRouter()

# In-memory storage (replace with database in production)
submissions_store: Dict[str, Dict] = {}
questions_store: Dict[str, Dict] = {}


def map_strategy_enum(strategy: StrategyEnum) -> GenerationStrategy:
    """Map API strategy enum to internal enum."""
    mapping = {
        StrategyEnum.ALL: GenerationStrategy.ALL,
        StrategyEnum.DIVERSE: GenerationStrategy.DIVERSE,
        StrategyEnum.FOCUSED: GenerationStrategy.FOCUSED,
        StrategyEnum.ADAPTIVE: GenerationStrategy.ADAPTIVE,
    }
    return mapping[strategy]


def map_level_enum(level: QuestionLevelEnum) -> QuestionLevel:
    """Map API level enum to internal enum."""
    mapping = {
        QuestionLevelEnum.ATOM: QuestionLevel.ATOM,
        QuestionLevelEnum.BLOCK: QuestionLevel.BLOCK,
        QuestionLevelEnum.RELATIONAL: QuestionLevel.RELATIONAL,
        QuestionLevelEnum.MACRO: QuestionLevel.MACRO,
    }
    return mapping[level]


def map_type_enum(qtype: QuestionTypeEnum) -> QuestionType:
    """Map API type enum to internal enum."""
    mapping = {
        QuestionTypeEnum.MULTIPLE_CHOICE: QuestionType.MULTIPLE_CHOICE,
        QuestionTypeEnum.FILL_IN_BLANK: QuestionType.FILL_IN_BLANK,
        QuestionTypeEnum.TRUE_FALSE: QuestionType.TRUE_FALSE,
        QuestionTypeEnum.SHORT_ANSWER: QuestionType.SHORT_ANSWER,
        QuestionTypeEnum.NUMERIC: QuestionType.NUMERIC,
        QuestionTypeEnum.CODE_SELECTION: QuestionType.CODE_SELECTION,
    }
    return mapping[qtype]


@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """
    Health check endpoint.

    Returns the status of the API and its components.
    """
    try:
        # Quick test of components
        from analyzers.static_analyzer import StaticAnalyzer
        from analyzers.dynamic_analyzer import DynamicAnalyzer
        from question_engine.templates import get_registry

        StaticAnalyzer()
        DynamicAnalyzer()
        registry = get_registry()

        return HealthResponse(
            status="healthy",
            version="1.0.0",
            components={
                "static_analyzer": "ok",
                "dynamic_analyzer": "ok",
                "template_system": "ok",
                "templates_loaded": str(len(registry.templates))
            }
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            version="1.0.0",
            components={"error": str(e)}
        )


@router.post(
    "/submit-code",
    response_model=CodeSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Questions"]
)
def submit_code(request: CodeSubmissionRequest):
    """
    Submit code and generate questions.

    This endpoint:
    1. Analyzes the submitted code (static + dynamic)
    2. Generates questions based on the code
    3. Returns questions with metadata

    **Example Request:**
    ```json
    {
        "code": "def factorial(n):\\n    if n <= 1:\\n        return 1\\n    return n * factorial(n - 1)\\n\\nresult = factorial(5)",
        "max_questions": 5,
        "strategy": "diverse"
    }
    ```

    **Example Response:**
    Returns a list of generated questions with metadata about the analysis.
    """
    try:
        # Create generation config from request
        config = GenerationConfig(
            max_questions=request.max_questions,
            strategy=map_strategy_enum(request.strategy)
        )

        # Apply filters if provided
        if request.allowed_levels:
            config.allowed_levels = {map_level_enum(l) for l in request.allowed_levels}

        if request.allowed_types:
            config.allowed_types = {map_type_enum(t) for t in request.allowed_types}

        if request.allowed_difficulties:
            config.allowed_difficulties = set(request.allowed_difficulties)

        # Generate questions
        generator = QuestionGenerator(config)
        result = generator.generate(request.code, request.test_inputs)

        # Generate unique submission ID
        submission_id = f"sub_{uuid.uuid4().hex[:12]}"

        # Convert questions to API format
        api_questions = []
        for i, question in enumerate(result.questions):
            question_id = f"q_{uuid.uuid4().hex[:12]}"

            # Convert answer choices
            answer_choices = [
                AnswerChoice(
                    text=choice.text,
                    is_correct=choice.is_correct,
                    explanation=choice.explanation
                )
                for choice in question.answer_choices
            ]

            api_question = Question(
                id=question_id,
                template_id=question.template_id,
                question_text=question.question_text,
                question_type=QuestionTypeEnum(question.question_type.value),
                question_level=QuestionLevelEnum(question.question_level.value),
                answer_type=question.answer_type.value,
                correct_answer=question.correct_answer,
                answer_choices=answer_choices,
                context=question.context,
                explanation=question.explanation,
                difficulty=question.difficulty
            )

            api_questions.append(api_question)

            # Store question for later answer checking
            questions_store[question_id] = {
                "submission_id": submission_id,
                "question": question,
                "api_question": api_question
            }

        # Create metadata
        metadata = GenerationMetadata(
            total_generated=result.total_generated,
            total_filtered=result.total_filtered,
            total_returned=len(result.questions),
            applicable_templates=result.applicable_templates,
            execution_successful=result.execution_successful,
            execution_time_ms=result.execution_time_ms
        )

        # Create analysis summary
        analysis_summary = AnalysisSummary()
        if result.static_analysis:
            summary = result.static_analysis.get('summary', {})
            analysis_summary.total_functions = summary.get('total_functions', 0)
            analysis_summary.total_variables = summary.get('total_variables', 0)
            analysis_summary.total_loops = summary.get('total_loops', 0)
            analysis_summary.total_conditionals = summary.get('total_conditionals', 0)
            analysis_summary.has_recursion = summary.get('has_recursion', False)

        if result.dynamic_analysis:
            analysis_summary.execution_successful = result.dynamic_analysis.get('execution_successful')
            analysis_summary.max_stack_depth = result.dynamic_analysis.get('max_stack_depth')

        # Store submission
        submissions_store[submission_id] = {
            "code": request.code,
            "questions": api_questions,
            "result": result,
            "metadata": metadata
        }

        # Create response
        response = CodeSubmissionResponse(
            submission_id=submission_id,
            questions=api_questions,
            metadata=metadata,
            analysis_summary=analysis_summary,
            errors=result.errors,
            warnings=result.warnings
        )

        return response

    except SyntaxError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Syntax error in code: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate questions: {str(e)}"
        )


@router.post(
    "/submit-answer",
    response_model=AnswerSubmissionResponse,
    tags=["Answers"]
)
def submit_answer(request: AnswerSubmissionRequest):
    """
    Submit an answer to a question and get feedback.

    **Example Request:**
    ```json
    {
        "submission_id": "sub_abc123",
        "question_id": "q_xyz789",
        "answer": "factorial"
    }
    ```

    **Example Response:**
    Returns feedback indicating if the answer is correct with an explanation.
    """
    # Check if question exists
    if request.question_id not in questions_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {request.question_id} not found"
        )

    question_data = questions_store[request.question_id]

    # Verify submission ID matches
    if question_data["submission_id"] != request.submission_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Submission ID does not match question"
        )

    question = question_data["question"]
    api_question = question_data["api_question"]

    # Check answer based on question type
    is_correct = False
    explanation = ""

    if api_question.question_type == QuestionTypeEnum.MULTIPLE_CHOICE:
        # For multiple choice, check if answer matches correct choice
        if isinstance(request.answer, str):
            is_correct = request.answer == str(question.correct_answer)
            if is_correct:
                explanation = f"Correct! {question.explanation or ''}"
            else:
                explanation = f"Incorrect. The correct answer is: {question.correct_answer}. {question.explanation or ''}"

    elif api_question.question_type == QuestionTypeEnum.NUMERIC:
        # For numeric, check if values are close enough
        try:
            user_answer = float(request.answer)
            correct_answer = float(question.correct_answer)
            is_correct = abs(user_answer - correct_answer) < 0.0001
            if is_correct:
                explanation = f"Correct! {question.explanation or ''}"
            else:
                explanation = f"Incorrect. The correct answer is: {correct_answer}. {question.explanation or ''}"
        except (ValueError, TypeError):
            explanation = "Invalid numeric answer format"

    elif api_question.question_type == QuestionTypeEnum.FILL_IN_BLANK:
        # For fill-in-blank, check string equality (case-insensitive)
        user_answer = str(request.answer).strip().lower()
        correct_answer = str(question.correct_answer).strip().lower()
        is_correct = user_answer == correct_answer
        if is_correct:
            explanation = f"Correct! {question.explanation or ''}"
        else:
            explanation = f"Incorrect. The correct answer is: {question.correct_answer}. {question.explanation or ''}"

    else:
        # For other types, basic string comparison
        is_correct = str(request.answer) == str(question.correct_answer)
        explanation = "Answer recorded" if is_correct else f"The expected answer is: {question.correct_answer}"

    feedback = AnswerFeedback(
        is_correct=is_correct,
        explanation=explanation,
        correct_answer=question.correct_answer if not is_correct else None
    )

    return AnswerSubmissionResponse(
        submission_id=request.submission_id,
        question_id=request.question_id,
        feedback=feedback
    )


@router.get(
    "/submission/{submission_id}",
    response_model=CodeSubmissionResponse,
    tags=["Questions"]
)
def get_submission(submission_id: str):
    """
    Retrieve a previous code submission and its questions.

    **Path Parameters:**
    - `submission_id`: The ID of the submission to retrieve

    **Example Response:**
    Returns the original submission with all its questions.
    """
    if submission_id not in submissions_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found"
        )

    submission = submissions_store[submission_id]
    result = submission["result"]

    # Reconstruct response
    analysis_summary = AnalysisSummary()
    if result.static_analysis:
        summary = result.static_analysis.get('summary', {})
        analysis_summary.total_functions = summary.get('total_functions', 0)
        analysis_summary.total_variables = summary.get('total_variables', 0)
        analysis_summary.total_loops = summary.get('total_loops', 0)
        analysis_summary.total_conditionals = summary.get('total_conditionals', 0)
        analysis_summary.has_recursion = summary.get('has_recursion', False)

    if result.dynamic_analysis:
        analysis_summary.execution_successful = result.dynamic_analysis.get('execution_successful')
        analysis_summary.max_stack_depth = result.dynamic_analysis.get('max_stack_depth')

    return CodeSubmissionResponse(
        submission_id=submission_id,
        questions=submission["questions"],
        metadata=submission["metadata"],
        analysis_summary=analysis_summary,
        errors=result.errors,
        warnings=result.warnings
    )


@router.get(
    "/templates",
    tags=["System"]
)
def list_templates():
    """
    List all available question templates.

    Returns information about each template including:
    - Template ID
    - Name and description
    - Question type and level
    - Difficulty

    **Example Response:**
    ```json
    {
        "templates": [
            {
                "id": "recursive_function_detection",
                "name": "Recursive Function Detection",
                "description": "Identify recursive functions",
                "type": "multiple_choice",
                "level": "block",
                "difficulty": "medium"
            }
        ]
    }
    ```
    """
    from question_engine.templates import get_registry

    registry = get_registry()
    templates = registry.list_templates()

    return {"templates": templates, "total": len(templates)}
