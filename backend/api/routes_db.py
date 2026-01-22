"""
API Routes with Database Persistence

Defines all REST API endpoints for the QLC system with database integration.
Now powered by AI-based question generation using OpenAI GPT-5.2.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, List
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
from question_engine.ai_generator import (
    AIQuestionGenerator,
    GenerationConfig,
)
from question_engine.answer_validator import (
    AnswerValidator,
    ValidationResult,
    MatchType,
)
from database import crud, get_db
from database.models import SubmissionStatus

# Create router
router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint.

    Returns the status of the API and its components.
    """
    try:
        # Quick test of components
        from analyzers.static_analyzer import StaticAnalyzer
        from analyzers.dynamic_analyzer import DynamicAnalyzer

        StaticAnalyzer()
        DynamicAnalyzer()

        # Test database connectivity
        await db.execute(text("SELECT 1"))

        return HealthResponse(
            status="healthy",
            version="2.0.0",
            components={
                "static_analyzer": "ok",
                "dynamic_analyzer": "ok",
                "ai_generator": "ok (GPT-5.2)",
                "database": "ok",
            }
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            version="2.0.0",
            components={"error": str(e)}
        )


@router.post(
    "/submit-code",
    response_model=CodeSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Questions"]
)
async def submit_code(
    request: CodeSubmissionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit code and generate questions using AI.

    This endpoint:
    1. Creates a code submission in the database
    2. Analyzes the submitted code (static + dynamic)
    3. Generates questions using OpenAI GPT-5.2
    4. Stores questions in the database
    5. Returns questions with metadata

    **Example Request:**
    ```json
    {
        "code": "def factorial(n):\\n    if n <= 1:\\n        return 1\\n    return n * factorial(n - 1)\\n\\nresult = factorial(5)",
        "max_questions": 5
    }
    ```

    **Example Response:**
    Returns a list of AI-generated questions with metadata about the analysis.
    """
    try:
        # Create submission record in database
        submission = await crud.create_submission(
            db,
            code=request.code,
            test_inputs=request.test_inputs,
            max_questions=request.max_questions,
            strategy=request.strategy.value if request.strategy else "diverse",
        )

        # Create generation config from request
        config = GenerationConfig(
            max_questions=request.max_questions or 10,
        )

        # Apply level filters if provided
        if request.allowed_levels:
            config.include_levels = [level.value for level in request.allowed_levels]

        # Apply type filters if provided
        if request.allowed_types:
            config.include_types = [t.value for t in request.allowed_types]

        # Apply difficulty filters if provided
        if request.allowed_difficulties:
            config.include_difficulties = request.allowed_difficulties

        # Generate questions using AI
        generator = AIQuestionGenerator(config)
        result = generator.generate(request.code, request.test_inputs)

        # Convert questions to API format and store in database
        api_questions = []
        for question in result.questions:
            # Create answer choices
            answer_choices_dicts = [
                {
                    "text": choice.text,
                    "is_correct": choice.is_correct,
                    "explanation": choice.explanation
                }
                for choice in question.answer_choices
            ]

            # Store question in database
            db_question = await crud.create_question(
                db,
                submission_id=submission.submission_id,
                template_id=question.template_id,
                question_text=question.question_text,
                question_type=question.question_type.value,
                question_level=question.question_level.value,
                answer_type=question.answer_type.value,
                correct_answer={"value": question.correct_answer},
                answer_choices=answer_choices_dicts,
                alternative_answers=question.alternative_answers,
                context=question.context,
                explanation=question.explanation,
                difficulty=question.difficulty
            )

            # Convert to API format
            answer_choices = [
                AnswerChoice(
                    text=choice["text"],
                    is_correct=choice["is_correct"],
                    explanation=choice.get("explanation")
                )
                for choice in answer_choices_dicts
            ]

            api_question = Question(
                id=db_question.question_id,
                template_id=db_question.template_id,
                question_text=db_question.question_text,
                question_type=QuestionTypeEnum(db_question.question_type),
                question_level=QuestionLevelEnum(db_question.question_level),
                answer_type=db_question.answer_type,
                correct_answer=db_question.correct_answer["value"],
                alternative_answers=db_question.alternative_answers or [],
                answer_choices=answer_choices,
                context=db_question.context,
                explanation=db_question.explanation,
                difficulty=db_question.difficulty
            )

            api_questions.append(api_question)

        # Create metadata
        metadata = GenerationMetadata(
            total_generated=result.total_generated,
            total_filtered=result.total_filtered,
            total_returned=len(result.questions),
            applicable_templates=1,  # AI generator acts as one template
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

        # Update submission with analysis results
        await crud.update_submission_analysis(
            db,
            submission_id=submission.submission_id,
            analysis_summary=analysis_summary.model_dump(),
            generation_metadata=metadata.model_dump(),
            errors=result.errors,
            warnings=result.warnings,
            status=SubmissionStatus.ANALYZED.value
        )

        # Commit the transaction
        await db.commit()

        # Create response
        response = CodeSubmissionResponse(
            submission_id=submission.submission_id,
            questions=api_questions,
            metadata=metadata,
            analysis_summary=analysis_summary,
            errors=result.errors,
            warnings=result.warnings
        )

        return response

    except SyntaxError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Syntax error in code: {str(e)}"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate questions: {str(e)}"
        )


@router.post(
    "/submit-answer",
    response_model=AnswerSubmissionResponse,
    tags=["Answers"]
)
async def submit_answer(
    request: AnswerSubmissionRequest,
    db: AsyncSession = Depends(get_db)
):
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
    try:
        # Get question from database
        question = await crud.get_question(db, request.question_id)

        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question {request.question_id} not found"
            )

        # Verify submission ID matches
        if question.submission_id != request.submission_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Submission ID does not match question"
            )

        # Check answer based on question type
        is_correct = False
        explanation = ""
        score = 0.0
        correct_answer_value = question.correct_answer.get("value")
        alternative_answers = question.alternative_answers or []

        question_type = QuestionTypeEnum(question.question_type)

        if question_type == QuestionTypeEnum.MULTIPLE_CHOICE:
            # For multiple choice, check if answer matches correct choice
            if isinstance(request.answer, str):
                is_correct = request.answer == str(correct_answer_value)
                score = 1.0 if is_correct else 0.0
                if is_correct:
                    explanation = f"Correct! {question.explanation or ''}"
                else:
                    explanation = f"Incorrect. The correct answer is: {correct_answer_value}. {question.explanation or ''}"

        elif question_type == QuestionTypeEnum.NUMERIC:
            # For numeric, check if values are close enough
            try:
                user_answer = float(request.answer)
                correct_answer = float(correct_answer_value)
                is_correct = abs(user_answer - correct_answer) < 0.0001
                score = 1.0 if is_correct else 0.0
                if is_correct:
                    explanation = f"Correct! {question.explanation or ''}"
                else:
                    explanation = f"Incorrect. The correct answer is: {correct_answer}. {question.explanation or ''}"
            except (ValueError, TypeError):
                explanation = "Invalid numeric answer format"

        elif question_type == QuestionTypeEnum.TRUE_FALSE:
            # For true/false questions
            user_answer = str(request.answer).strip().lower()
            correct_answer = str(correct_answer_value).strip().lower()
            is_correct = user_answer == correct_answer
            score = 1.0 if is_correct else 0.0
            if is_correct:
                explanation = f"Correct! {question.explanation or ''}"
            else:
                explanation = f"Incorrect. The correct answer is: {correct_answer_value}. {question.explanation or ''}"

        elif question_type in [QuestionTypeEnum.FILL_IN_BLANK, QuestionTypeEnum.SHORT_ANSWER]:
            # For open-ended questions, use the semantic answer validator
            validator = AnswerValidator(case_sensitive=False, allow_partial=True)
            validation_result = validator.validate(
                student_answer=str(request.answer),
                correct_answer=str(correct_answer_value),
                alternative_answers=alternative_answers,
                question_type=question_type.value
            )

            is_correct = validation_result.is_correct
            score = validation_result.confidence if is_correct else 0.0

            if is_correct:
                if validation_result.match_type == MatchType.PARTIAL:
                    explanation = f"Correct! Your answer captures the key concept. {question.explanation or ''}"
                elif validation_result.match_type == MatchType.ALTERNATIVE:
                    explanation = f"Correct! {question.explanation or ''}"
                else:
                    explanation = f"Correct! {question.explanation or ''}"
            else:
                # Show the primary answer, but note that alternatives exist
                if alternative_answers:
                    explanation = f"Incorrect. The correct answer is: {correct_answer_value} (other acceptable answers include: {', '.join(alternative_answers[:3])}). {question.explanation or ''}"
                else:
                    explanation = f"Incorrect. The correct answer is: {correct_answer_value}. {question.explanation or ''}"

        else:
            # For other types (CODE_SELECTION), basic string comparison
            is_correct = str(request.answer) == str(correct_answer_value)
            score = 1.0 if is_correct else 0.0
            explanation = "Answer recorded" if is_correct else f"The expected answer is: {correct_answer_value}"

        # Store answer in database
        await crud.create_answer(
            db,
            submission_id=request.submission_id,
            question_id=request.question_id,
            student_answer={"value": request.answer},
            is_correct=is_correct,
            score=score,
            feedback=explanation
        )

        await db.commit()

        feedback = AnswerFeedback(
            is_correct=is_correct,
            explanation=explanation,
            correct_answer=correct_answer_value if not is_correct else None
        )

        return AnswerSubmissionResponse(
            submission_id=request.submission_id,
            question_id=request.question_id,
            feedback=feedback
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit answer: {str(e)}"
        )


@router.get(
    "/submission/{submission_id}",
    response_model=CodeSubmissionResponse,
    tags=["Questions"]
)
async def get_submission_endpoint(
    submission_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a previous code submission and its questions.

    **Path Parameters:**
    - `submission_id`: The ID of the submission to retrieve

    **Example Response:**
    Returns the original submission with all its questions.
    """
    # Get submission from database
    submission = await crud.get_submission(db, submission_id, include_questions=True)

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found"
        )

    # Convert questions to API format
    api_questions = []
    for db_question in submission.questions:
        answer_choices = [
            AnswerChoice(
                text=choice["text"],
                is_correct=choice["is_correct"],
                explanation=choice.get("explanation")
            )
            for choice in db_question.answer_choices
        ]

        api_question = Question(
            id=db_question.question_id,
            template_id=db_question.template_id,
            question_text=db_question.question_text,
            question_type=QuestionTypeEnum(db_question.question_type),
            question_level=QuestionLevelEnum(db_question.question_level),
            answer_type=db_question.answer_type,
            correct_answer=db_question.correct_answer.get("value"),
            alternative_answers=db_question.alternative_answers or [],
            answer_choices=answer_choices,
            context=db_question.context,
            explanation=db_question.explanation,
            difficulty=db_question.difficulty
        )

        api_questions.append(api_question)

    # Create metadata and analysis summary from stored data
    metadata = GenerationMetadata(**submission.generation_metadata) if submission.generation_metadata else GenerationMetadata(
        total_generated=len(api_questions),
        total_filtered=0,
        total_returned=len(api_questions),
        applicable_templates=1,
        execution_successful=True,
        execution_time_ms=0.0
    )

    analysis_summary = AnalysisSummary(**submission.analysis_summary) if submission.analysis_summary else AnalysisSummary()

    return CodeSubmissionResponse(
        submission_id=submission.submission_id,
        questions=api_questions,
        metadata=metadata,
        analysis_summary=analysis_summary,
        errors=submission.errors or [],
        warnings=submission.warnings or []
    )


@router.get(
    "/submissions",
    tags=["Questions"]
)
async def list_submissions(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List all code submissions.

    **Query Parameters:**
    - `skip`: Number of records to skip (default: 0)
    - `limit`: Maximum number of records to return (default: 100)
    - `status`: Filter by status (pending, analyzed, completed, failed)

    **Example Response:**
    Returns a list of submissions with basic information.
    """
    submissions = await crud.list_submissions(db, skip=skip, limit=limit, status=status)

    return {
        "submissions": [
            {
                "submission_id": s.submission_id,
                "status": s.status,
                "created_at": s.created_at.isoformat(),
                "question_count": len(s.questions) if hasattr(s, 'questions') else 0
            }
            for s in submissions
        ],
        "total": len(submissions),
        "skip": skip,
        "limit": limit
    }


@router.get(
    "/templates",
    tags=["System"]
)
def list_templates():
    """
    List available question generation system.

    Returns information about the AI-powered question generation system.

    **Example Response:**
    ```json
    {
        "templates": [
            {
                "id": "ai_powered_generator",
                "name": "AI-Powered Question Generator",
                "description": "Uses OpenAI GPT-5.2 to generate contextual comprehension questions",
                "type": "all",
                "level": "all",
                "difficulty": "adaptive"
            }
        ]
    }
    ```
    """
    return {
        "templates": [
            {
                "id": "ai_powered_generator",
                "name": "AI-Powered Question Generator",
                "description": "Uses OpenAI GPT-5.2 to generate contextual comprehension questions based on static and dynamic code analysis",
                "type": "all",
                "level": "all",
                "difficulty": "adaptive"
            }
        ],
        "total": 1,
        "note": "Question generation is now powered by AI. The system uses static and dynamic analysis results to generate pedagogically valuable questions."
    }
