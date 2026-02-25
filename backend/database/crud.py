"""
Database CRUD operations for submissions, questions, and answer choices.
"""

import json

from sqlalchemy.orm import Session

from .models import AnswerChoice, Question, Submission


def save_submission(
    db: Session,
    submission_id: str,
    code: str,
    result,          # GenerationResult (internal)
    api_questions,   # list[Question]  (Pydantic API model)
    metadata,        # GenerationMetadata (Pydantic)
) -> None:
    """
    Persist a code submission and all its questions + answer choices.

    Each multiple-choice question gets 1 correct row and up to 3 distractor rows
    in answer_choices, enabling later SQL distractor-quality analysis.
    """
    db_submission = Submission(
        id=submission_id,
        code=code,
        execution_time_ms=metadata.execution_time_ms,
        total_questions=len(api_questions),
        errors=json.dumps(result.errors) if result.errors else None,
    )
    db.add(db_submission)

    for api_q in api_questions:
        db_question = Question(
            id=api_q.id,
            submission_id=submission_id,
            question_text=api_q.question_text,
            question_type=api_q.question_type.value,
            question_level=api_q.question_level.value,
            correct_answer=str(api_q.correct_answer),
            difficulty=api_q.difficulty,
            explanation=api_q.explanation,
        )
        db.add(db_question)

        for choice in api_q.answer_choices:
            db.add(AnswerChoice(
                question_id=api_q.id,
                text=choice.text,
                is_correct=choice.is_correct,
                explanation=choice.explanation,
            ))

    db.commit()
