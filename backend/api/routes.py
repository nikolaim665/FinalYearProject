"""
API Routes

Defines all REST API endpoints for the QLC system.
Now powered by the LangGraph multi-agent pipeline.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict
import uuid
import sys
import time
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
    StrategyEnum,
    QuestionEvaluationResponse,
    EvaluationResultResponse,
)
from database import get_db
from database import crud as db_crud

# Create router
router = APIRouter()

# In-memory storage for quick answer checking and submission retrieval
submissions_store: Dict[str, Dict] = {}
questions_store: Dict[str, Dict] = {}


def _build_config(request: CodeSubmissionRequest) -> dict:
    """Build the GenerationConfig dict from a CodeSubmissionRequest."""
    cfg: dict = {
        "max_questions": request.max_questions,
        "enable_caching": True,
        "enable_auto_driver": True,
        # Model assignments (can be overridden via env/config in the future)
        "question_model": "gpt-4o",
        "answer_model": "gpt-4o",
        "explanation_model": "gpt-4o-mini",
        "judge_model": "gpt-4o",
        "driver_model": "gpt-4o-mini",
    }
    if request.allowed_levels:
        cfg["include_levels"] = [l.value for l in request.allowed_levels]
    if request.allowed_types:
        cfg["include_types"] = [t.value for t in request.allowed_types]
    if request.allowed_difficulties:
        cfg["include_difficulties"] = list(request.allowed_difficulties)
    return cfg


def _state_to_response(
    submission_id: str,
    state: dict,
    request: CodeSubmissionRequest,
) -> CodeSubmissionResponse:
    """Convert a final QLCState dict into a CodeSubmissionResponse."""
    questions_complete: list = state.get("questions_complete", [])
    static_analysis: dict = state.get("static_analysis") or {}
    dynamic_analysis: dict = state.get("dynamic_analysis") or {}
    errors: list = state.get("analysis_errors", [])
    warnings: list = state.get("analysis_warnings", [])
    from_cache: bool = state.get("from_cache", False)
    rag_used: bool = state.get("rag_context") is not None

    api_questions = []
    for i, q in enumerate(questions_complete):
        question_id = q.get("id") or f"q_{uuid.uuid4().hex[:12]}"

        # Build answer choices
        answer_choices = [
            AnswerChoice(
                text=c.get("text", ""),
                is_correct=c.get("is_correct", False),
                explanation=c.get("explanation"),
            )
            for c in q.get("answer_choices", [])
        ]

        # Determine answer_type from question_type
        q_type_str = q.get("question_type", "multiple_choice")
        answer_type = "choice"

        try:
            q_type_enum = QuestionTypeEnum(q_type_str)
        except ValueError:
            q_type_enum = QuestionTypeEnum.MULTIPLE_CHOICE

        try:
            q_level_enum = QuestionLevelEnum(q.get("question_level", "block"))
        except ValueError:
            q_level_enum = QuestionLevelEnum.BLOCK

        api_question = Question(
            id=question_id,
            template_id=q.get("template_id", f"ai_generated_{q.get('question_level', 'block')}"),
            question_text=q.get("question_text", ""),
            question_type=q_type_enum,
            question_level=q_level_enum,
            answer_type=answer_type,
            correct_answer=q.get("correct_answer", ""),
            answer_choices=answer_choices,
            context=q.get("context") or {},
            explanation=q.get("explanation"),
            difficulty=q.get("difficulty", "medium"),
        )

        api_questions.append(api_question)

        # Store for answer submission
        questions_store[question_id] = {
            "submission_id": submission_id,
            "correct_answer": q.get("correct_answer", ""),
            "question_type": q_type_enum,
            "explanation": q.get("explanation", ""),
            "api_question": api_question,
        }

    # Analysis summary
    analysis_summary = AnalysisSummary()
    if static_analysis:
        summary = static_analysis.get("summary", {})
        analysis_summary.total_functions = summary.get("total_functions", 0)
        analysis_summary.total_variables = summary.get("total_variables", 0)
        analysis_summary.total_loops = summary.get("total_loops", 0)
        analysis_summary.total_conditionals = summary.get("total_conditionals", 0)
        analysis_summary.has_recursion = summary.get("has_recursion", False)
    if dynamic_analysis:
        analysis_summary.execution_successful = dynamic_analysis.get("execution_successful")
        analysis_summary.max_stack_depth = dynamic_analysis.get("max_stack_depth")

    agents_used = ["analyzer", "question", "answer", "explanation"]
    if state.get("evaluation"):
        agents_used.append("judge")

    metadata = GenerationMetadata(
        total_generated=len(questions_complete),
        total_filtered=0,
        total_returned=len(api_questions),
        applicable_templates=1,
        execution_successful=dynamic_analysis.get("execution_successful", True)
            if dynamic_analysis else True,
        execution_time_ms=state.get("execution_time_ms", 0.0),
        rag_used=rag_used,
        agents_used=agents_used,
    )

    return CodeSubmissionResponse(
        submission_id=submission_id,
        questions=api_questions,
        metadata=metadata,
        analysis_summary=analysis_summary,
        errors=errors,
        warnings=warnings,
    )


@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Health check endpoint."""
    try:
        from analyzers.static_analyzer import StaticAnalyzer
        from analyzers.dynamic_analyzer import DynamicAnalyzer
        from question_engine.templates import get_registry

        StaticAnalyzer()
        DynamicAnalyzer()
        registry = get_registry()

        return HealthResponse(
            status="healthy",
            version="2.0.0",
            components={
                "static_analyzer": "ok",
                "dynamic_analyzer": "ok",
                "template_system": "ok",
                "pipeline": "langgraph",
                "templates_loaded": str(len(registry.templates)),
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
def submit_code(request: CodeSubmissionRequest, db: Session = Depends(get_db)):
    """
    Submit code and generate questions via the LangGraph multi-agent pipeline.

    The pipeline runs 4 agents in sequence:
    1. Analyzer Agent — static + dynamic analysis
    2. Question Agent — generates question text
    3. Answer Agent — generates correct answers + distractors
    4. Explanation Agent — generates answer explanations
    (Judge Agent runs in the same graph after explanations)

    **Example Request:**
    ```json
    {
        "code": "def factorial(n):\\n    if n <= 1:\\n        return 1\\n    return n * factorial(n - 1)\\n\\nresult = factorial(5)",
        "max_questions": 5,
        "strategy": "diverse"
    }
    ```
    """
    try:
        from question_engine.graph import run_pipeline

        config = _build_config(request)

        # Run the LangGraph pipeline
        final_state = run_pipeline(
            source_code=request.code,
            max_questions=request.max_questions,
            lecture_slides=request.lecture_slides,
            config=config,
        )

        # Check for fatal analysis errors
        errors = final_state.get("analysis_errors", [])
        if errors and not final_state.get("questions_complete"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Code analysis failed: {'; '.join(errors)}"
            )

        submission_id = f"sub_{uuid.uuid4().hex[:12]}"

        response = _state_to_response(submission_id, final_state, request)

        # Persist to database using a compat result dict
        try:
            db_crud.save_submission(
                db,
                submission_id,
                request.code,
                final_state,
                response.questions,
                response.metadata,
            )
        except Exception as db_err:
            # DB persistence failure is non-fatal
            import logging
            logging.getLogger(__name__).warning("DB persistence failed: %s", db_err)

        # Store in-memory for answer checking and retrieval
        submissions_store[submission_id] = {
            "code": request.code,
            "questions": response.questions,
            "state": final_state,
            "metadata": response.metadata,
        }

        return response

    except HTTPException:
        raise
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
    """Submit an answer to a question and get feedback."""
    if request.question_id not in questions_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {request.question_id} not found"
        )

    question_data = questions_store[request.question_id]

    if question_data["submission_id"] != request.submission_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Submission ID does not match question"
        )

    correct_answer = question_data["correct_answer"]
    question_type = question_data["question_type"]
    explanation_text = question_data.get("explanation", "")

    is_correct = False

    if question_type == QuestionTypeEnum.NUMERIC:
        try:
            user_val = float(request.answer)
            correct_val = float(correct_answer)
            is_correct = abs(user_val - correct_val) < 0.0001
        except (ValueError, TypeError):
            pass
    else:
        is_correct = str(request.answer).strip() == str(correct_answer).strip()

    if is_correct:
        explanation = f"Correct! {explanation_text}".strip()
    else:
        explanation = f"Incorrect. The correct answer is: {correct_answer}. {explanation_text}".strip()

    feedback = AnswerFeedback(
        is_correct=is_correct,
        explanation=explanation,
        correct_answer=correct_answer if not is_correct else None,
    )

    return AnswerSubmissionResponse(
        submission_id=request.submission_id,
        question_id=request.question_id,
        feedback=feedback,
    )


@router.get(
    "/submission/{submission_id}",
    response_model=CodeSubmissionResponse,
    tags=["Questions"]
)
def get_submission(submission_id: str):
    """Retrieve a previous code submission and its questions."""
    if submission_id not in submissions_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found"
        )

    submission = submissions_store[submission_id]
    state = submission.get("state", {})
    static_analysis = state.get("static_analysis") or {}
    dynamic_analysis = state.get("dynamic_analysis") or {}

    analysis_summary = AnalysisSummary()
    if static_analysis:
        summary = static_analysis.get("summary", {})
        analysis_summary.total_functions = summary.get("total_functions", 0)
        analysis_summary.total_variables = summary.get("total_variables", 0)
        analysis_summary.total_loops = summary.get("total_loops", 0)
        analysis_summary.total_conditionals = summary.get("total_conditionals", 0)
        analysis_summary.has_recursion = summary.get("has_recursion", False)
    if dynamic_analysis:
        analysis_summary.execution_successful = dynamic_analysis.get("execution_successful")
        analysis_summary.max_stack_depth = dynamic_analysis.get("max_stack_depth")

    return CodeSubmissionResponse(
        submission_id=submission_id,
        questions=submission["questions"],
        metadata=submission["metadata"],
        analysis_summary=analysis_summary,
        errors=state.get("analysis_errors", []),
        warnings=state.get("analysis_warnings", []),
    )


@router.post(
    "/evaluate/{submission_id}",
    response_model=EvaluationResultResponse,
    tags=["Evaluation"]
)
def evaluate_submission(submission_id: str):
    """
    Retrieve the LLM judge evaluation for a submission.

    The judge agent runs as part of the pipeline after question generation.
    This endpoint returns the stored evaluation results.
    If the evaluation is not yet available, it runs the judge synchronously.
    """
    if submission_id not in submissions_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found"
        )

    submission = submissions_store[submission_id]
    state = submission.get("state", {})
    evaluation = state.get("evaluation")

    # If no evaluation stored (e.g. cache hit), run judge on demand
    if not evaluation:
        try:
            from question_engine.agents.judge_agent import judge_agent_node
            judge_result = judge_agent_node(state)
            evaluation = judge_result.get("evaluation")
            # Update stored state
            state["evaluation"] = evaluation
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Evaluation failed: {str(e)}"
            )

    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not available for this submission"
        )

    question_evaluations = [
        QuestionEvaluationResponse(
            question_id=e.get("question_id", ""),
            question_text=e.get("question_text", ""),
            scores=e.get("scores", {}),
            overall_score=e.get("overall_score", 0.0),
            explanation=e.get("explanation", ""),
            issues=e.get("issues", []),
            is_flagged=e.get("is_flagged", False),
        )
        for e in evaluation.get("question_evaluations", [])
    ]

    return EvaluationResultResponse(
        submission_id=submission_id,
        question_evaluations=question_evaluations,
        aggregate=evaluation.get("aggregate", {}),
        tokens_used=evaluation.get("tokens_used", 0),
        evaluation_time_ms=evaluation.get("evaluation_time_ms", 0.0),
    )


@router.get(
    "/templates",
    tags=["System"]
)
def list_templates():
    """List available question generation information."""
    return {
        "templates": [
            {
                "id": "langgraph_pipeline",
                "name": "LangGraph Multi-Agent Pipeline",
                "description": (
                    "Uses a 4-agent LangGraph pipeline: "
                    "Analyzer → Question → Answer → Explanation. "
                    "Optional RAG with lecture slides."
                ),
                "type": "multiple_choice",
                "level": "all",
                "difficulty": "adaptive",
                "agents": ["analyzer", "question", "answer", "explanation", "judge"],
            }
        ],
        "total": 1,
    }
