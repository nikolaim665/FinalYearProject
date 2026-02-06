"""
SQLAlchemy Database Models

Defines the database schema for code submissions, questions, and answers.
"""

from datetime import datetime, timezone
from typing import Optional
import json

from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator, TEXT
import enum


class JSONEncodedDict(TypeDecorator):
    """Custom type for storing JSON data as TEXT."""

    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Convert Python dict to JSON string."""
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        """Convert JSON string to Python dict."""
        if value is not None:
            return json.loads(value)
        return value


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class QuestionLevel(str, enum.Enum):
    """Question difficulty level."""
    ATOM = "atom"
    BLOCK = "block"
    RELATIONAL = "relational"
    MACRO = "macro"


class QuestionType(str, enum.Enum):
    """Type of question."""
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_IN_BLANK = "fill_in_blank"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    NUMERIC = "numeric"
    CODE_SELECTION = "code_selection"


class SubmissionStatus(str, enum.Enum):
    """Status of code submission."""
    PENDING = "pending"
    ANALYZED = "analyzed"
    COMPLETED = "completed"
    FAILED = "failed"


class CodeSubmission(Base):
    """
    Represents a student code submission.

    Stores the submitted code, analysis results, and metadata.
    """

    __tablename__ = "code_submissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    submission_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # Code and analysis
    code: Mapped[str] = mapped_column(Text, nullable=False)
    test_inputs: Mapped[Optional[dict]] = mapped_column(JSONEncodedDict, nullable=True)

    # Analysis results
    analysis_summary: Mapped[Optional[dict]] = mapped_column(JSONEncodedDict, nullable=True)
    generation_metadata: Mapped[Optional[dict]] = mapped_column(JSONEncodedDict, nullable=True)
    errors: Mapped[Optional[list]] = mapped_column(JSONEncodedDict, nullable=True, default=list)
    warnings: Mapped[Optional[list]] = mapped_column(JSONEncodedDict, nullable=True, default=list)

    # Status and timing
    status: Mapped[str] = mapped_column(
        SQLEnum(SubmissionStatus, values_callable=lambda x: [e.value for e in x]),
        default=SubmissionStatus.PENDING.value,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Configuration
    max_questions: Mapped[int] = mapped_column(Integer, default=10)
    strategy: Mapped[str] = mapped_column(String(50), default="diverse")

    # Relationships
    questions: Mapped[list["Question"]] = relationship(
        "Question",
        back_populates="submission",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CodeSubmission(id={self.submission_id}, status={self.status})>"


class Question(Base):
    """
    Represents a generated question about student code.

    Linked to a code submission and can have multiple student answers.

    The correct_answer field stores a JSON object with:
    - value: The primary correct answer
    - alternative_answers: List of alternative acceptable answers (for open-ended questions)
    - case_sensitive: Whether answer comparison is case-sensitive (default False)
    - partial_match: Whether partial matching is allowed (default False)
    """

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # Foreign key
    submission_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("code_submissions.submission_id", ondelete="CASCADE"),
        nullable=False
    )

    # Question content
    template_id: Mapped[str] = mapped_column(String(100), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(
        SQLEnum(QuestionType, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    question_level: Mapped[str] = mapped_column(
        SQLEnum(QuestionLevel, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )

    # Answer information
    answer_type: Mapped[str] = mapped_column(String(50), nullable=False)
    correct_answer: Mapped[dict] = mapped_column(JSONEncodedDict, nullable=False)
    # Alternative acceptable answers for open-ended questions
    alternative_answers: Mapped[Optional[list]] = mapped_column(JSONEncodedDict, nullable=True, default=list)
    answer_choices: Mapped[list] = mapped_column(JSONEncodedDict, nullable=True, default=list)

    # Additional context
    context: Mapped[dict] = mapped_column(JSONEncodedDict, nullable=True, default=dict)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")

    # Rich explanation from the answer explainer LLM
    answer_explanation: Mapped[Optional[dict]] = mapped_column(JSONEncodedDict, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    submission: Mapped["CodeSubmission"] = relationship(
        "CodeSubmission",
        back_populates="questions"
    )
    answers: Mapped[list["Answer"]] = relationship(
        "Answer",
        back_populates="question",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Question(id={self.question_id}, type={self.question_type})>"


class Answer(Base):
    """
    Represents a student's answer to a question.

    Stores the answer, grading result, and feedback.
    """

    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    answer_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # Foreign keys
    submission_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("code_submissions.submission_id", ondelete="CASCADE"),
        nullable=False
    )
    question_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("questions.question_id", ondelete="CASCADE"),
        nullable=False
    )

    # Answer content
    student_answer: Mapped[dict] = mapped_column(JSONEncodedDict, nullable=False)

    # Grading
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # For partial credit
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    graded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    question: Mapped["Question"] = relationship(
        "Question",
        back_populates="answers"
    )

    def __repr__(self) -> str:
        return f"<Answer(id={self.answer_id}, correct={self.is_correct})>"
