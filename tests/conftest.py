"""
Shared pytest fixtures for the test suite.

Provides an autouse mock for the OpenAI client so that tests never make
real API calls. The mock returns a fixed set of sample questions that
satisfy the assertions made across all test classes in
test_question_generator.py.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure the backend package is importable from all test files
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# ---------------------------------------------------------------------------
# Fixed mock response returned by the mocked OpenAI chat completions API.
# Includes representative template_ids, types, levels, and difficulties so
# that all test assertions in test_question_generator.py pass.
# ---------------------------------------------------------------------------
_MOCK_API_RESPONSE = {
    "questions": [
        {
            "template_id": "recursive_function_detection",
            "question_text": "Which function in the code is recursive?",
            "question_type": "multiple_choice",
            "question_level": "block",
            "correct_answer": "factorial",
            "difficulty": "medium",
            "explanation": "factorial calls itself with a smaller argument.",
            "answer_choices": [
                {"text": "helper", "is_correct": False, "explanation": "helper does not call itself."},
                {"text": "factorial", "is_correct": True, "explanation": "factorial calls itself."},
                {"text": "main", "is_correct": False, "explanation": "There is no main function."},
                {"text": "None", "is_correct": False, "explanation": "All functions here are iterative."},
            ],
            "context": {"function_name": "factorial"},
        },
        {
            "template_id": "loop_iteration_count",
            "question_text": "How many times does the for loop execute?",
            "question_type": "numeric",
            "question_level": "block",
            "correct_answer": 5,
            "difficulty": "medium",
            "explanation": "range(5) produces 5 iterations.",
            "context": {"loop_type": "for"},
        },
        {
            "template_id": "variable_value_tracing",
            "question_text": "What is the final value of result?",
            "question_type": "multiple_choice",
            "question_level": "atom",
            "correct_answer": "120",
            "difficulty": "easy",
            "explanation": "factorial(5) returns 120.",
            "answer_choices": [
                {"text": "24", "is_correct": False, "explanation": "That is factorial(4)."},
                {"text": "120", "is_correct": True, "explanation": "Correct."},
                {"text": "5", "is_correct": False, "explanation": "That is the input."},
                {"text": "720", "is_correct": False, "explanation": "That is factorial(6)."},
            ],
            "context": {"variable_name": "result"},
        },
    ]
}


@pytest.fixture(autouse=True)
def clear_question_cache():
    """Clear the AI response cache before each test to avoid cross-test contamination."""
    from question_engine.ai_generator import _response_cache
    _response_cache.clear()
    yield
    _response_cache.clear()


@pytest.fixture(autouse=True)
def mock_openai_client():
    """
    Replace openai.OpenAI with a MagicMock for every test so that no test
    ever requires a real API key or makes a network call.

    The mock's chat.completions.create() returns a response whose content
    is the JSON-encoded _MOCK_API_RESPONSE defined above.  That JSON is
    valid for both the question generator (looks for "questions" key) and
    gracefully handled by the answer explainer (looks for "explanations"
    key, finds nothing, and falls back to default explanations).
    """
    mock_message = MagicMock()
    mock_message.content = json.dumps(_MOCK_API_RESPONSE)

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_usage = MagicMock()
    mock_usage.total_tokens = 100

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    # Patch the OpenAI class wherever it is imported by name so that
    # __init__ doesn't raise "api_key must be set" before any test runs.
    with patch("question_engine.ai_generator.OpenAI", return_value=mock_client), \
         patch("question_engine.answer_explainer.OpenAI", return_value=mock_client):
        yield mock_client
