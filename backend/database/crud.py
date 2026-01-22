"""
CRUD Operations

Database operations for code submissions, questions, and answers.
"""

from typing import Optional, List
from datetime import datetime, timezone
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from .models import CodeSubmission, Question, Answer, SubmissionStatus


# CodeSubmission CRUD

async def create_submission(
    db: AsyncSession,
    code: str,
    test_inputs: Optional[dict] = None,
    max_questions: int = 10,
    strategy: str = "diverse",
) -> CodeSubmission:
    """
    Create a new code submission.

    Args:
        db: Database session
        code: Python source code
        test_inputs: Optional test inputs
        max_questions: Maximum questions to generate
        strategy: Question selection strategy

    Returns:
        Created CodeSubmission instance
    """
    submission_id = f"sub_{uuid.uuid4().hex[:12]}"

    submission = CodeSubmission(
        submission_id=submission_id,
        code=code,
        test_inputs=test_inputs,
        max_questions=max_questions,
        strategy=strategy,
        status=SubmissionStatus.PENDING.value,
    )

    db.add(submission)
    await db.flush()  # Get the ID without committing
    await db.refresh(submission)

    return submission


async def get_submission(
    db: AsyncSession,
    submission_id: str,
    include_questions: bool = False,
) -> Optional[CodeSubmission]:
    """
    Get a code submission by ID.

    Args:
        db: Database session
        submission_id: Submission ID
        include_questions: Whether to include related questions

    Returns:
        CodeSubmission or None if not found
    """
    query = select(CodeSubmission).where(
        CodeSubmission.submission_id == submission_id
    )

    if include_questions:
        query = query.options(
            selectinload(CodeSubmission.questions).selectinload(Question.answers)
        )

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def update_submission_analysis(
    db: AsyncSession,
    submission_id: str,
    analysis_summary: dict,
    generation_metadata: dict,
    errors: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None,
    status: str = SubmissionStatus.ANALYZED.value,
) -> Optional[CodeSubmission]:
    """
    Update submission with analysis results.

    Args:
        db: Database session
        submission_id: Submission ID
        analysis_summary: Summary of code analysis
        generation_metadata: Question generation metadata
        errors: List of errors
        warnings: List of warnings
        status: Updated status

    Returns:
        Updated CodeSubmission or None if not found
    """
    submission = await get_submission(db, submission_id)
    if not submission:
        return None

    submission.analysis_summary = analysis_summary
    submission.generation_metadata = generation_metadata
    submission.errors = errors or []
    submission.warnings = warnings or []
    submission.status = status
    submission.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(submission)

    return submission


async def list_submissions(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
) -> List[CodeSubmission]:
    """
    List code submissions with optional filtering.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Optional status filter

    Returns:
        List of CodeSubmission instances
    """
    query = select(CodeSubmission).order_by(CodeSubmission.created_at.desc())

    if status:
        query = query.where(CodeSubmission.status == status)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


# Question CRUD

async def create_question(
    db: AsyncSession,
    submission_id: str,
    template_id: str,
    question_text: str,
    question_type: str,
    question_level: str,
    answer_type: str,
    correct_answer: dict,
    answer_choices: Optional[List[dict]] = None,
    alternative_answers: Optional[List[str]] = None,
    context: Optional[dict] = None,
    explanation: Optional[str] = None,
    difficulty: str = "medium",
) -> Question:
    """
    Create a new question.

    Args:
        db: Database session
        submission_id: Associated submission ID
        template_id: Question template ID
        question_text: Question text
        question_type: Type of question
        question_level: Question level
        answer_type: Type of answer
        correct_answer: Correct answer
        answer_choices: Optional answer choices (for multiple choice)
        alternative_answers: Optional list of alternative acceptable answers
        context: Optional context dict
        explanation: Optional explanation
        difficulty: Difficulty level

    Returns:
        Created Question instance
    """
    question_id = f"q_{uuid.uuid4().hex[:12]}"

    question = Question(
        question_id=question_id,
        submission_id=submission_id,
        template_id=template_id,
        question_text=question_text,
        question_type=question_type,
        question_level=question_level,
        answer_type=answer_type,
        correct_answer=correct_answer,
        answer_choices=answer_choices or [],
        alternative_answers=alternative_answers or [],
        context=context or {},
        explanation=explanation,
        difficulty=difficulty,
    )

    db.add(question)
    await db.flush()
    await db.refresh(question)

    return question


async def get_question(
    db: AsyncSession,
    question_id: str,
    include_answers: bool = False,
) -> Optional[Question]:
    """
    Get a question by ID.

    Args:
        db: Database session
        question_id: Question ID
        include_answers: Whether to include student answers

    Returns:
        Question or None if not found
    """
    query = select(Question).where(Question.question_id == question_id)

    if include_answers:
        query = query.options(selectinload(Question.answers))

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_submission_questions(
    db: AsyncSession,
    submission_id: str,
) -> List[Question]:
    """
    Get all questions for a submission.

    Args:
        db: Database session
        submission_id: Submission ID

    Returns:
        List of Question instances
    """
    query = (
        select(Question)
        .where(Question.submission_id == submission_id)
        .order_by(Question.created_at)
    )

    result = await db.execute(query)
    return list(result.scalars().all())


# Answer CRUD

async def create_answer(
    db: AsyncSession,
    submission_id: str,
    question_id: str,
    student_answer: dict,
    is_correct: Optional[bool] = None,
    score: Optional[float] = None,
    feedback: Optional[str] = None,
) -> Answer:
    """
    Create a new answer.

    Args:
        db: Database session
        submission_id: Associated submission ID
        question_id: Associated question ID
        student_answer: Student's answer
        is_correct: Whether answer is correct
        score: Optional score (0-1)
        feedback: Optional feedback

    Returns:
        Created Answer instance
    """
    answer_id = f"ans_{uuid.uuid4().hex[:12]}"

    answer = Answer(
        answer_id=answer_id,
        submission_id=submission_id,
        question_id=question_id,
        student_answer=student_answer,
        is_correct=is_correct,
        score=score,
        feedback=feedback,
    )

    if is_correct is not None:
        answer.graded_at = datetime.now(timezone.utc)

    db.add(answer)
    await db.flush()
    await db.refresh(answer)

    return answer


async def get_answer(
    db: AsyncSession,
    answer_id: str,
) -> Optional[Answer]:
    """
    Get an answer by ID.

    Args:
        db: Database session
        answer_id: Answer ID

    Returns:
        Answer or None if not found
    """
    query = select(Answer).where(Answer.answer_id == answer_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def update_answer_grading(
    db: AsyncSession,
    answer_id: str,
    is_correct: bool,
    score: Optional[float] = None,
    feedback: Optional[str] = None,
) -> Optional[Answer]:
    """
    Update answer grading results.

    Args:
        db: Database session
        answer_id: Answer ID
        is_correct: Whether answer is correct
        score: Optional score (0-1)
        feedback: Optional feedback

    Returns:
        Updated Answer or None if not found
    """
    answer = await get_answer(db, answer_id)
    if not answer:
        return None

    answer.is_correct = is_correct
    answer.score = score
    answer.feedback = feedback
    answer.graded_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(answer)

    return answer


async def get_question_answers(
    db: AsyncSession,
    question_id: str,
) -> List[Answer]:
    """
    Get all answers for a question.

    Args:
        db: Database session
        question_id: Question ID

    Returns:
        List of Answer instances
    """
    query = (
        select(Answer)
        .where(Answer.question_id == question_id)
        .order_by(Answer.submitted_at)
    )

    result = await db.execute(query)
    return list(result.scalars().all())
