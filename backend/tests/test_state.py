"""
Tests for QLCState TypedDict and make_initial_state().
"""

import pytest
from question_engine.state import QLCState, make_initial_state


def test_make_initial_state_defaults():
    state = make_initial_state("x = 5")
    assert state["source_code"] == "x = 5"
    assert state["max_questions"] == 10
    assert state["lecture_slides"] is None
    assert state["config"] == {}
    assert state["rag_context"] is None
    assert state["static_analysis"] is None
    assert state["dynamic_analysis"] is None
    assert state["analysis_warnings"] == []
    assert state["analysis_errors"] == []
    assert state["questions"] == []
    assert state["questions_with_answers"] == []
    assert state["questions_complete"] == []
    assert state["evaluation"] is None
    assert state["tokens_used"] == 0
    assert state["execution_time_ms"] == 0.0
    assert state["from_cache"] is False


def test_make_initial_state_with_params():
    cfg = {"enable_caching": False, "question_model": "gpt-4o"}
    state = make_initial_state(
        source_code="def foo(): pass",
        max_questions=5,
        lecture_slides="Lecture 1: Functions",
        config=cfg,
    )
    assert state["max_questions"] == 5
    assert state["lecture_slides"] == "Lecture 1: Functions"
    assert state["config"] == cfg


def test_state_has_all_required_keys():
    state = make_initial_state("pass")
    required = [
        "source_code", "lecture_slides", "max_questions", "config",
        "rag_context", "static_analysis", "dynamic_analysis",
        "analysis_warnings", "analysis_errors", "questions",
        "questions_with_answers", "questions_complete", "evaluation",
        "tokens_used", "execution_time_ms", "from_cache",
    ]
    for key in required:
        assert key in state, f"Missing key: {key}"


def test_state_list_fields_are_mutable():
    state = make_initial_state("pass")
    state["analysis_warnings"].append("test warning")
    assert "test warning" in state["analysis_warnings"]
    state["questions"].append({"question_text": "q?"})
    assert len(state["questions"]) == 1
