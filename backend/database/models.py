"""
SQLAlchemy ORM models for the QLC database.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(String, primary_key=True)
    code = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    execution_time_ms = Column(Float)
    total_questions = Column(Integer)
    errors = Column(Text)  # JSON-encoded list

    questions = relationship("Question", back_populates="submission", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(String, primary_key=True)
    submission_id = Column(String, ForeignKey("submissions.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String, nullable=False)   # multiple_choice | true_false | numeric
    question_level = Column(String, nullable=False)  # atom | block | relational | macro
    correct_answer = Column(Text, nullable=False)
    difficulty = Column(String)
    explanation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    submission = relationship("Submission", back_populates="questions")
    answer_choices = relationship("AnswerChoice", back_populates="question", cascade="all, delete-orphan")


class AnswerChoice(Base):
    """
    Stores all answer choices for a question — 1 correct + up to 3 distractors.

    Use is_correct=False rows to analyse distractor quality:
        SELECT q.question_text, ac.text, ac.explanation
        FROM answer_choices ac
        JOIN questions q ON ac.question_id = q.id
        WHERE ac.is_correct = 0;
    """

    __tablename__ = "answer_choices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(String, ForeignKey("questions.id"), nullable=False)
    text = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    explanation = Column(Text)  # why this choice is right / why it is a plausible distractor

    question = relationship("Question", back_populates="answer_choices")
