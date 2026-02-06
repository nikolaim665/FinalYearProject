"""
API Routes

Defines all REST API endpoints for the QLC system.
Powered by AI-based question generation using OpenAI GPT-5.2.
Uses in-memory storage.
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
    AnswerExplanationDetail,
    WrongAnswerExplanation,
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

# Create router
router = APIRouter()

# In-memory storage
submissions_store: Dict[str, Dict] = {}
questions_store: Dict[str, Dict] = {}


@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """
    Health check endpoint.

    Returns the status of the API and its components.
    """
    try:
        from analyzers.static_analyzer import StaticAnalyzer
        from analyzers.dynamic_analyzer import DynamicAnalyzer

        StaticAnalyzer()
        DynamicAnalyzer()

        return HealthResponse(
            status="healthy",
            version="2.0.0",
            components={
                "static_analyzer": "ok",
                "dynamic_analyzer": "ok",
                "ai_generator": "ok (GPT-5.2)",
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
def submit_code(request: CodeSubmissionRequest):
    """
    Submit code and generate questions using AI.

    This endpoint:
    1. Analyzes the submitted code (static + dynamic)
    2. Generates questions using OpenAI GPT-5.2
    3. Returns questions with metadata
    """
    try:
        # Create generation config from request
        config = GenerationConfig(
            max_questions=request.max_questions or 10,
        )

        if request.allowed_levels:
            config.include_levels = [level.value for level in request.allowed_levels]

        if request.allowed_types:
            config.include_types = [t.value for t in request.allowed_types]

        if request.allowed_difficulties:
            config.include_difficulties = request.allowed_difficulties

        # Generate questions using AI
        generator = AIQuestionGenerator(config)
        result = generator.generate(request.code, request.test_inputs)

        # Generate unique submission ID
        submission_id = f"sub_{uuid.uuid4().hex[:12]}"

        # Convert questions to API format
        api_questions = []
        for i, question in enumerate(result.questions):
            question_id = f"q_{uuid.uuid4().hex[:12]}"

            # Create answer choices
            answer_choices_dicts = [
                {
                    "text": choice.text,
                    "is_correct": choice.is_correct,
                    "explanation": choice.explanation
                }
                for choice in question.answer_choices
            ]

            # Get the answer explanation for this question (if available)
            answer_explanation_dict = None
            if i < len(result.answer_explanations):
                exp = result.answer_explanations[i]
                if hasattr(exp, 'to_dict'):
                    answer_explanation_dict = exp.to_dict()
                elif isinstance(exp, dict):
                    answer_explanation_dict = exp

            # Convert to API format
            answer_choices = [
                AnswerChoice(
                    text=choice["text"],
                    is_correct=choice["is_correct"],
                    explanation=choice.get("explanation")
                )
                for choice in answer_choices_dicts
            ]

            # Build the AnswerExplanationDetail for the API response
            api_answer_explanation = None
            if answer_explanation_dict:
                api_answer_explanation = AnswerExplanationDetail(
                    verified_correct_answer=answer_explanation_dict.get("verified_correct_answer"),
                    is_answer_verified=answer_explanation_dict.get("is_answer_verified", True),
                    correct_answer_reasoning=answer_explanation_dict.get("correct_answer_reasoning", ""),
                    code_references=answer_explanation_dict.get("code_references", []),
                    analysis_references=answer_explanation_dict.get("analysis_references", []),
                    wrong_answer_explanations=[
                        WrongAnswerExplanation(**we)
                        for we in answer_explanation_dict.get("wrong_answer_explanations", [])
                    ],
                    learning_tip=answer_explanation_dict.get("learning_tip"),
                    corrected_answer=answer_explanation_dict.get("corrected_answer"),
                )

            api_question = Question(
                id=question_id,
                template_id=question.template_id,
                question_text=question.question_text,
                question_type=QuestionTypeEnum(question.question_type.value),
                question_level=QuestionLevelEnum(question.question_level.value),
                answer_type=question.answer_type.value,
                correct_answer=question.correct_answer,
                alternative_answers=question.alternative_answers or [],
                answer_choices=answer_choices,
                context=question.context,
                explanation=question.explanation,
                difficulty=question.difficulty,
                answer_explanation=api_answer_explanation,
            )

            api_questions.append(api_question)

            # Store question for later answer checking
            questions_store[question_id] = {
                "submission_id": submission_id,
                "question": question,
                "api_question": api_question,
                "answer_explanation": answer_explanation_dict,
            }

        # Create metadata
        metadata = GenerationMetadata(
            total_generated=result.total_generated,
            total_filtered=result.total_filtered,
            total_returned=len(result.questions),
            applicable_templates=1,
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

        # Store submission in memory
        submissions_store[submission_id] = {
            "code": request.code,
            "questions": api_questions,
            "metadata": metadata,
            "analysis_summary": analysis_summary,
            "errors": result.errors,
            "warnings": result.warnings,
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
    answer_exp = question_data.get("answer_explanation") or {}

    # Check answer based on question type
    is_correct = False
    explanation = ""
    correct_answer_value = question.correct_answer
    alternative_answers = question.alternative_answers or []

    if api_question.question_type == QuestionTypeEnum.MULTIPLE_CHOICE:
        if isinstance(request.answer, str):
            is_correct = request.answer == str(correct_answer_value)
            if is_correct:
                reasoning = answer_exp.get("correct_answer_reasoning", "")
                explanation = f"Correct! {reasoning or question.explanation or ''}"
            else:
                wrong_exp = ""
                for we in answer_exp.get("wrong_answer_explanations", []):
                    if we.get("answer_text") == request.answer:
                        wrong_exp = we.get("explanation", "")
                        break
                reasoning = answer_exp.get("correct_answer_reasoning", question.explanation or "")
                if wrong_exp:
                    explanation = f"Incorrect. {wrong_exp} The correct answer is: {correct_answer_value}. {reasoning}"
                else:
                    explanation = f"Incorrect. The correct answer is: {correct_answer_value}. {reasoning}"

    elif api_question.question_type == QuestionTypeEnum.NUMERIC:
        try:
            user_answer = float(request.answer)
            correct_answer = float(correct_answer_value)
            is_correct = abs(user_answer - correct_answer) < 0.0001
            if is_correct:
                explanation = f"Correct! {question.explanation or ''}"
            else:
                explanation = f"Incorrect. The correct answer is: {correct_answer}. {question.explanation or ''}"
        except (ValueError, TypeError):
            explanation = "Invalid numeric answer format"

    elif api_question.question_type == QuestionTypeEnum.TRUE_FALSE:
        user_answer = str(request.answer).strip().lower()
        correct_answer = str(correct_answer_value).strip().lower()
        is_correct = user_answer == correct_answer
        if is_correct:
            explanation = f"Correct! {question.explanation or ''}"
        else:
            explanation = f"Incorrect. The correct answer is: {correct_answer_value}. {question.explanation or ''}"

    elif api_question.question_type in [QuestionTypeEnum.FILL_IN_BLANK, QuestionTypeEnum.SHORT_ANSWER]:
        validator = AnswerValidator(case_sensitive=False, allow_partial=True)
        validation_result = validator.validate(
            student_answer=str(request.answer),
            correct_answer=str(correct_answer_value),
            alternative_answers=alternative_answers,
            question_type=api_question.question_type.value
        )

        is_correct = validation_result.is_correct

        if is_correct:
            if validation_result.match_type == MatchType.PARTIAL:
                explanation = f"Correct! Your answer captures the key concept. {question.explanation or ''}"
            elif validation_result.match_type == MatchType.ALTERNATIVE:
                explanation = f"Correct! {question.explanation or ''}"
            else:
                explanation = f"Correct! {question.explanation or ''}"
        else:
            if alternative_answers:
                explanation = f"Incorrect. The correct answer is: {correct_answer_value} (other acceptable answers include: {', '.join(alternative_answers[:3])}). {question.explanation or ''}"
            else:
                explanation = f"Incorrect. The correct answer is: {correct_answer_value}. {question.explanation or ''}"

    else:
        is_correct = str(request.answer) == str(correct_answer_value)
        explanation = "Answer recorded" if is_correct else f"The expected answer is: {correct_answer_value}"

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


@router.get(
    "/submission/{submission_id}",
    response_model=CodeSubmissionResponse,
    tags=["Questions"]
)
def get_submission(submission_id: str):
    """
    Retrieve a previous code submission and its questions.
    """
    if submission_id not in submissions_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found"
        )

    submission = submissions_store[submission_id]

    return CodeSubmissionResponse(
        submission_id=submission_id,
        questions=submission["questions"],
        metadata=submission["metadata"],
        analysis_summary=submission["analysis_summary"],
        errors=submission.get("errors", []),
        warnings=submission.get("warnings", [])
    )


@router.get(
    "/submissions",
    tags=["Questions"]
)
def list_submissions(
    skip: int = 0,
    limit: int = 100,
):
    """
    List all code submissions (from current session).
    """
    all_ids = list(submissions_store.keys())
    paginated = all_ids[skip:skip + limit]

    return {
        "submissions": [
            {
                "submission_id": sid,
                "status": "analyzed",
                "question_count": len(submissions_store[sid]["questions"])
            }
            for sid in paginated
        ],
        "total": len(all_ids),
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
