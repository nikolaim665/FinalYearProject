"""
Tests for the LangGraph QLC pipeline (graph.py).

Uses mocked LLM calls so no OpenAI API key is required.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from question_engine.state import make_initial_state, QLCState
from question_engine.graph import (
    build_qlc_graph,
    route_rag,
    check_analysis_success,
    _cache_key,
    _check_cache,
    _store_cache,
    _response_cache,
)


# ---------------------------------------------------------------------------
# Routing logic tests (pure functions, no LLM needed)
# ---------------------------------------------------------------------------

class TestRouteRag:
    def test_no_slides_routes_to_analyzer(self):
        state = make_initial_state("x = 5")
        assert route_rag(state) == "analyzer_agent"

    def test_with_slides_routes_to_rag(self):
        state = make_initial_state("x = 5", lecture_slides="Lecture content")
        assert route_rag(state) == "rag_retrieve"

    def test_empty_string_slides_routes_to_analyzer(self):
        state = make_initial_state("x = 5", lecture_slides="")
        # Empty string is falsy
        assert route_rag(state) == "analyzer_agent"


class TestCheckAnalysisSuccess:
    def test_both_failed_returns_error(self):
        state = make_initial_state("bad code")
        state["static_analysis"] = {"error": "SyntaxError"}
        state["dynamic_analysis"] = {"execution_successful": False, "error": "failed"}
        state["analysis_errors"] = ["Both failed"]
        assert check_analysis_success(state) == "error"

    def test_static_ok_returns_continue(self):
        state = make_initial_state("x = 5")
        state["static_analysis"] = {"summary": {"total_functions": 0}}
        state["dynamic_analysis"] = {"execution_successful": True}
        assert check_analysis_success(state) == "continue"

    def test_only_dynamic_failed_still_continues(self):
        state = make_initial_state("x = 5")
        state["static_analysis"] = {"summary": {"total_functions": 0}}
        state["dynamic_analysis"] = {"execution_successful": False}
        # Only one failed, no fatal errors → continue
        assert check_analysis_success(state) == "continue"

    def test_static_none_dynamic_failed_with_errors_is_error(self):
        state = make_initial_state("bad")
        state["static_analysis"] = None
        state["dynamic_analysis"] = {"execution_successful": False}
        state["analysis_errors"] = ["Static failed"]
        assert check_analysis_success(state) == "error"


class TestCaching:
    def test_cache_key_is_deterministic(self):
        state = make_initial_state("x = 5", max_questions=3)
        key1 = _cache_key(state)
        key2 = _cache_key(state)
        assert key1 == key2

    def test_cache_key_differs_on_different_code(self):
        s1 = make_initial_state("x = 5")
        s2 = make_initial_state("y = 10")
        assert _cache_key(s1) != _cache_key(s2)

    def test_cache_miss_returns_none(self):
        state = make_initial_state("unique_code_xyz_12345")
        _response_cache.clear()
        assert _check_cache(state) is None

    def test_cache_store_and_retrieve(self):
        state = make_initial_state("def cached(): pass")
        _response_cache.clear()
        data = {"questions_complete": [{"question_text": "q?"}]}
        _store_cache(state, data)
        result = _check_cache(state)
        assert result is not None
        assert result["questions_complete"][0]["question_text"] == "q?"

    def test_caching_disabled_skips_cache(self):
        state = make_initial_state("x = 5", config={"enable_caching": False})
        _response_cache.clear()
        _store_cache(state, {"questions_complete": []})
        # Should not be stored when disabled
        assert _check_cache(state) is None


class TestGraphCompilation:
    def test_graph_compiles(self):
        g = build_qlc_graph()
        assert g is not None

    def test_graph_type_is_compiled_state_graph(self):
        from langgraph.graph.state import CompiledStateGraph
        g = build_qlc_graph()
        assert isinstance(g, CompiledStateGraph)


class TestAnalyzerAgentNode:
    """Test the analyzer agent node in isolation (no LLM calls)."""

    def test_static_analysis_runs_on_simple_code(self):
        from question_engine.agents.analyzer_agent import analyzer_agent_node
        state = make_initial_state("x = 5\nprint(x)")
        result = analyzer_agent_node(state)
        assert "static_analysis" in result
        assert "dynamic_analysis" in result
        assert "analysis_warnings" in result
        assert "analysis_errors" in result

    def test_static_analysis_on_function_code(self):
        from question_engine.agents.analyzer_agent import analyzer_agent_node
        state = make_initial_state("def add(a, b):\n    return a + b\nresult = add(1, 2)")
        result = analyzer_agent_node(state)
        assert result["static_analysis"] is not None
        assert result["dynamic_analysis"] is not None
        assert result["dynamic_analysis"].get("execution_successful") is True

    def test_syntax_error_code_sets_errors(self):
        from question_engine.agents.analyzer_agent import analyzer_agent_node
        state = make_initial_state("def broken(:")
        result = analyzer_agent_node(state)
        # Should have errors or warnings but not crash
        assert isinstance(result["analysis_errors"], list) or isinstance(result["analysis_warnings"], list)


class TestQuestionAgentNode:
    """Test question agent node with mocked LLM."""

    def test_returns_questions_list(self):
        from question_engine.agents.question_agent import question_agent_node

        mock_questions = {
            "questions": [
                {
                    "question_text": "What is x?",
                    "question_type": "multiple_choice",
                    "question_level": "atom",
                    "difficulty": "easy",
                    "context": {"line_number": 1, "variable_name": "x"},
                    "template_id": "ai_generated_atom",
                }
            ]
        }

        mock_response = MagicMock()
        mock_response.content = json.dumps(mock_questions)
        mock_response.usage_metadata = {"total_tokens": 100}

        with patch("question_engine.agents.question_agent.ChatOpenAI") as MockLLM:
            MockLLM.return_value.invoke.return_value = mock_response
            state = make_initial_state("x = 5")
            state["static_analysis"] = {"summary": {}, "functions": []}
            state["dynamic_analysis"] = {"execution_successful": True, "final_variables": {"x": 5}}
            result = question_agent_node(state)

        assert "questions" in result
        assert len(result["questions"]) == 1
        assert result["questions"][0]["question_text"] == "What is x?"
        assert result["tokens_used"] == 100

    def test_handles_json_parse_error_gracefully(self):
        from question_engine.agents.question_agent import question_agent_node

        mock_response = MagicMock()
        mock_response.content = "not valid json at all !!!"
        mock_response.usage_metadata = None

        with patch("question_engine.agents.question_agent.ChatOpenAI") as MockLLM:
            MockLLM.return_value.invoke.return_value = mock_response
            state = make_initial_state("x = 5")
            state["static_analysis"] = {"summary": {}}
            state["dynamic_analysis"] = {"execution_successful": True}
            result = question_agent_node(state)

        # Should return empty questions rather than raising
        assert result["questions"] == []


class TestAnswerAgentNode:
    """Test answer agent node with mocked LLM."""

    def test_merges_answers_into_questions(self):
        from question_engine.agents.answer_agent import answer_agent_node

        mock_answers = {
            "answers": [
                {
                    "question_index": 0,
                    "correct_answer": {"text": "5", "verified": True, "verification_method": "dynamic_analysis"},
                    "distractors": [
                        {"text": "4", "misconception_targeted": "off-by-one"},
                        {"text": "6", "misconception_targeted": "inclusive range"},
                        {"text": "10", "misconception_targeted": "list length"},
                    ],
                }
            ]
        }

        mock_response = MagicMock()
        mock_response.content = json.dumps(mock_answers)
        mock_response.usage_metadata = {"total_tokens": 150}

        with patch("question_engine.agents.answer_agent.ChatOpenAI") as MockLLM:
            MockLLM.return_value.invoke.return_value = mock_response
            state = make_initial_state("for i in range(5): pass")
            state["questions"] = [{"question_text": "How many times?", "question_level": "block"}]
            state["static_analysis"] = {"summary": {}}
            state["dynamic_analysis"] = {"execution_successful": True, "final_variables": {}}
            result = answer_agent_node(state)

        assert "questions_with_answers" in result
        qwa = result["questions_with_answers"]
        assert len(qwa) == 1
        assert qwa[0]["correct_answer"] == "5"
        choices = qwa[0]["answer_choices"]
        assert any(c["is_correct"] for c in choices)
        assert sum(1 for c in choices if not c["is_correct"]) == 3


class TestExplanationAgentNode:
    """Test explanation agent node with mocked LLM."""

    def test_adds_explanations_to_choices(self):
        from question_engine.agents.explanation_agent import explanation_agent_node

        mock_explanations = {
            "explanations": [
                {
                    "question_index": 0,
                    "correct_answer_explanation": "range(5) produces 5 values.",
                    "distractor_explanations": [
                        {"distractor_text": "4", "why_wrong": "Off by one.", "learning_tip": "Count from 0."},
                    ],
                }
            ]
        }

        mock_response = MagicMock()
        mock_response.content = json.dumps(mock_explanations)
        mock_response.usage_metadata = {"total_tokens": 80}

        with patch("question_engine.agents.explanation_agent.ChatOpenAI") as MockLLM:
            MockLLM.return_value.invoke.return_value = mock_response
            state = make_initial_state("for i in range(5): pass")
            state["questions_with_answers"] = [
                {
                    "question_text": "How many times?",
                    "correct_answer": "5",
                    "answer_choices": [
                        {"text": "5", "is_correct": True},
                        {"text": "4", "is_correct": False},
                    ],
                }
            ]
            result = explanation_agent_node(state)

        assert "questions_complete" in result
        qc = result["questions_complete"]
        assert len(qc) == 1
        assert qc[0]["explanation"] == "range(5) produces 5 values."
        # Check distractor explanation was added
        distractor = next(c for c in qc[0]["answer_choices"] if not c["is_correct"])
        assert "Off by one" in distractor.get("explanation", "")
