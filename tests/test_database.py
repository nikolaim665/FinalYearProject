"""
Tests for Database Models and CRUD Operations

Tests the database layer including models, session management, and CRUD operations.
"""

import pytest
import pytest_asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from database import crud, init_db, drop_db
from database.models import CodeSubmission, Question, Answer, SubmissionStatus
from database.session import AsyncSessionLocal


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session."""
    # Initialize test database
    await init_db()

    # Create session
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()

    # Clean up
    await drop_db()


@pytest.mark.asyncio
async def test_create_submission(db_session):
    """Test creating a code submission."""
    submission = await crud.create_submission(
        db_session,
        code="def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)",
        max_questions=5,
        strategy="diverse"
    )

    assert submission.submission_id.startswith("sub_")
    assert submission.code is not None
    assert submission.max_questions == 5
    assert submission.strategy == "diverse"
    assert submission.status == SubmissionStatus.PENDING.value


@pytest.mark.asyncio
async def test_get_submission(db_session):
    """Test retrieving a submission."""
    # Create submission
    created = await crud.create_submission(
        db_session,
        code="print('hello')",
        max_questions=3
    )
    await db_session.commit()

    # Retrieve submission
    retrieved = await crud.get_submission(db_session, created.submission_id)

    assert retrieved is not None
    assert retrieved.submission_id == created.submission_id
    assert retrieved.code == "print('hello')"


@pytest.mark.asyncio
async def test_update_submission_analysis(db_session):
    """Test updating submission with analysis results."""
    # Create submission
    submission = await crud.create_submission(
        db_session,
        code="x = 5",
        max_questions=2
    )
    await db_session.commit()

    # Update with analysis
    updated = await crud.update_submission_analysis(
        db_session,
        submission_id=submission.submission_id,
        analysis_summary={"total_functions": 0, "total_variables": 1},
        generation_metadata={"total_generated": 2, "total_returned": 2},
        errors=[],
        warnings=["No functions found"],
        status=SubmissionStatus.ANALYZED.value
    )

    assert updated is not None
    assert updated.status == SubmissionStatus.ANALYZED.value
    assert updated.analysis_summary["total_variables"] == 1
    assert "No functions found" in updated.warnings


@pytest.mark.asyncio
async def test_create_question(db_session):
    """Test creating a question."""
    # Create submission first
    submission = await crud.create_submission(
        db_session,
        code="def test(): pass"
    )
    await db_session.commit()

    # Create question
    question = await crud.create_question(
        db_session,
        submission_id=submission.submission_id,
        template_id="test_template",
        question_text="What does this function do?",
        question_type="multiple_choice",
        question_level="block",
        answer_type="static",
        correct_answer={"value": "nothing"},
        answer_choices=[
            {"text": "nothing", "is_correct": True},
            {"text": "something", "is_correct": False}
        ],
        difficulty="easy"
    )

    assert question.question_id.startswith("q_")
    assert question.submission_id == submission.submission_id
    assert question.question_text == "What does this function do?"
    assert question.difficulty == "easy"


@pytest.mark.asyncio
async def test_get_submission_questions(db_session):
    """Test retrieving all questions for a submission."""
    # Create submission
    submission = await crud.create_submission(
        db_session,
        code="def test(): pass"
    )
    await db_session.commit()

    # Create multiple questions
    for i in range(3):
        await crud.create_question(
            db_session,
            submission_id=submission.submission_id,
            template_id=f"template_{i}",
            question_text=f"Question {i}",
            question_type="multiple_choice",
            question_level="atom",
            answer_type="static",
            correct_answer={"value": f"answer_{i}"}
        )
    await db_session.commit()

    # Retrieve questions
    questions = await crud.get_submission_questions(
        db_session,
        submission.submission_id
    )

    assert len(questions) == 3
    assert all(q.submission_id == submission.submission_id for q in questions)


@pytest.mark.asyncio
async def test_create_answer(db_session):
    """Test creating an answer."""
    # Create submission and question
    submission = await crud.create_submission(
        db_session,
        code="x = 42"
    )
    await db_session.commit()

    question = await crud.create_question(
        db_session,
        submission_id=submission.submission_id,
        template_id="test_template",
        question_text="What is x?",
        question_type="numeric",
        question_level="atom",
        answer_type="static",
        correct_answer={"value": 42}
    )
    await db_session.commit()

    # Create answer
    answer = await crud.create_answer(
        db_session,
        submission_id=submission.submission_id,
        question_id=question.question_id,
        student_answer={"value": 42},
        is_correct=True,
        score=1.0,
        feedback="Correct!"
    )

    assert answer.answer_id.startswith("ans_")
    assert answer.question_id == question.question_id
    assert answer.is_correct is True
    assert answer.score == 1.0
    assert answer.graded_at is not None


@pytest.mark.asyncio
async def test_update_answer_grading(db_session):
    """Test updating answer grading."""
    # Create submission, question, and answer
    submission = await crud.create_submission(
        db_session,
        code="y = 10"
    )
    await db_session.commit()

    question = await crud.create_question(
        db_session,
        submission_id=submission.submission_id,
        template_id="test_template",
        question_text="What is y?",
        question_type="numeric",
        question_level="atom",
        answer_type="static",
        correct_answer={"value": 10}
    )
    await db_session.commit()

    answer = await crud.create_answer(
        db_session,
        submission_id=submission.submission_id,
        question_id=question.question_id,
        student_answer={"value": 9}
    )
    await db_session.commit()

    # Update grading
    updated = await crud.update_answer_grading(
        db_session,
        answer_id=answer.answer_id,
        is_correct=False,
        score=0.0,
        feedback="Incorrect, the correct answer is 10"
    )

    assert updated is not None
    assert updated.is_correct is False
    assert updated.score == 0.0
    assert "Incorrect" in updated.feedback


@pytest.mark.asyncio
async def test_cascade_delete(db_session):
    """Test that deleting a submission cascades to questions and answers."""
    # Create submission with question and answer
    submission = await crud.create_submission(
        db_session,
        code="z = 100"
    )
    await db_session.commit()

    question = await crud.create_question(
        db_session,
        submission_id=submission.submission_id,
        template_id="test_template",
        question_text="What is z?",
        question_type="numeric",
        question_level="atom",
        answer_type="static",
        correct_answer={"value": 100}
    )
    await db_session.commit()

    answer = await crud.create_answer(
        db_session,
        submission_id=submission.submission_id,
        question_id=question.question_id,
        student_answer={"value": 100},
        is_correct=True
    )
    await db_session.commit()

    # Delete submission
    await db_session.delete(submission)
    await db_session.commit()

    # Verify question and answer are also deleted
    retrieved_question = await crud.get_question(db_session, question.question_id)
    retrieved_answer = await crud.get_answer(db_session, answer.answer_id)

    assert retrieved_question is None
    assert retrieved_answer is None


@pytest.mark.asyncio
async def test_list_submissions(db_session):
    """Test listing submissions with pagination."""
    # Create multiple submissions
    for i in range(5):
        await crud.create_submission(
            db_session,
            code=f"x = {i}",
            max_questions=1
        )
    await db_session.commit()

    # List with pagination
    submissions_page1 = await crud.list_submissions(db_session, skip=0, limit=3)
    submissions_page2 = await crud.list_submissions(db_session, skip=3, limit=3)

    assert len(submissions_page1) == 3
    assert len(submissions_page2) == 2  # Only 2 remaining


@pytest.mark.asyncio
async def test_json_encoded_dict_storage(db_session):
    """Test that JSONEncodedDict properly stores and retrieves complex data."""
    submission = await crud.create_submission(
        db_session,
        code="def test(): pass",
        test_inputs={
            "function": "test",
            "args": [1, 2, 3],
            "kwargs": {"key": "value"}
        }
    )
    await db_session.commit()

    # Retrieve and verify
    retrieved = await crud.get_submission(db_session, submission.submission_id)

    assert retrieved.test_inputs is not None
    assert retrieved.test_inputs["function"] == "test"
    assert retrieved.test_inputs["args"] == [1, 2, 3]
    assert retrieved.test_inputs["kwargs"]["key"] == "value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
