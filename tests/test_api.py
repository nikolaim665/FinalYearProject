"""
Tests for REST API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from api.app import app

# Create test client
client = TestClient(app)


class TestHealthEndpoint:
    """Tests for /api/health endpoint."""

    def test_health_check(self):
        """Health check should return 200 OK."""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "components" in data


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root(self):
        """Root endpoint should return API info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data


class TestSubmitCodeEndpoint:
    """Tests for /api/submit-code endpoint."""

    def test_submit_valid_code(self):
        """Should generate questions for valid code."""
        request_data = {
            "code": """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def helper(x):
    return x

result = factorial(5)
""",
            "max_questions": 10
        }

        response = client.post("/api/submit-code", json=request_data)

        assert response.status_code == 201
        data = response.json()

        # Check response structure
        assert "submission_id" in data
        assert "questions" in data
        assert "metadata" in data
        assert "analysis_summary" in data

        # Check submission ID
        assert data["submission_id"].startswith("sub_")

        # Check questions
        assert len(data["questions"]) > 0
        for question in data["questions"]:
            assert "id" in question
            assert "question_text" in question
            assert "question_type" in question
            assert "correct_answer" in question

        # Check metadata
        metadata = data["metadata"]
        assert "total_generated" in metadata
        assert "total_returned" in metadata
        assert "execution_successful" in metadata

    def test_submit_code_with_strategy(self):
        """Should accept different strategies."""
        request_data = {
            "code": "x = 5\ny = x * 2",
            "max_questions": 5,
            "strategy": "diverse"
        }

        response = client.post("/api/submit-code", json=request_data)

        assert response.status_code == 201

    def test_submit_code_with_filters(self):
        """Should accept level and type filters."""
        request_data = {
            "code": """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
""",
            "max_questions": 10,
            "allowed_levels": ["block"],
            "allowed_difficulties": ["medium"]
        }

        response = client.post("/api/submit-code", json=request_data)

        assert response.status_code == 201
        data = response.json()

        # All questions should be block level
        for question in data["questions"]:
            assert question["question_level"] == "block"

    def test_submit_empty_code(self):
        """Should reject empty code."""
        request_data = {
            "code": "   ",
            "max_questions": 5
        }

        response = client.post("/api/submit-code", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_submit_code_with_runtime_error(self):
        """Should handle runtime errors and still return questions."""
        request_data = {
            "code": """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
crash = 1 / 0
""",
            "max_questions": 5
        }

        response = client.post("/api/submit-code", json=request_data)

        assert response.status_code == 201
        data = response.json()

        # Should have warnings about execution failure
        assert len(data["warnings"]) > 0

        # But should still have questions from static analysis
        # (might be 0 if no static templates match)
        assert "questions" in data

    def test_submit_code_with_test_inputs(self):
        """Should accept test inputs for dynamic analysis."""
        request_data = {
            "code": "result = input_value * 2",
            "test_inputs": {"input_value": 10},
            "max_questions": 5
        }

        response = client.post("/api/submit-code", json=request_data)

        assert response.status_code == 201


class TestSubmitAnswerEndpoint:
    """Tests for /api/submit-answer endpoint."""

    def test_submit_correct_answer(self):
        """Should validate correct answers."""
        # First, submit code to get questions
        code_request = {
            "code": """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def helper(x):
    return x

result = factorial(5)
""",
            "max_questions": 10
        }

        code_response = client.post("/api/submit-code", json=code_request)
        code_data = code_response.json()

        submission_id = code_data["submission_id"]
        questions = code_data["questions"]

        # Find a multiple choice question about recursion
        recursive_question = None
        for q in questions:
            if q["template_id"] == "recursive_function_detection":
                recursive_question = q
                break

        if recursive_question:
            # Submit correct answer
            answer_request = {
                "submission_id": submission_id,
                "question_id": recursive_question["id"],
                "answer": "factorial"
            }

            answer_response = client.post("/api/submit-answer", json=answer_request)

            assert answer_response.status_code == 200
            answer_data = answer_response.json()

            assert "feedback" in answer_data
            feedback = answer_data["feedback"]
            assert "is_correct" in feedback
            # factorial is recursive, so should be correct
            assert feedback["is_correct"] is True

    def test_submit_incorrect_answer(self):
        """Should validate incorrect answers."""
        # Submit code
        code_request = {
            "code": """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def helper(x):
    return x

result = factorial(5)
""",
            "max_questions": 10
        }

        code_response = client.post("/api/submit-code", json=code_request)
        code_data = code_response.json()

        if len(code_data["questions"]) > 0:
            question = code_data["questions"][0]

            # Submit wrong answer
            answer_request = {
                "submission_id": code_data["submission_id"],
                "question_id": question["id"],
                "answer": "definitely_wrong_answer"
            }

            answer_response = client.post("/api/submit-answer", json=answer_request)

            assert answer_response.status_code == 200
            answer_data = answer_response.json()

            feedback = answer_data["feedback"]
            # Most likely incorrect
            if not feedback["is_correct"]:
                assert feedback["correct_answer"] is not None

    def test_submit_answer_invalid_question_id(self):
        """Should reject invalid question IDs."""
        answer_request = {
            "submission_id": "sub_123",
            "question_id": "q_invalid",
            "answer": "test"
        }

        response = client.post("/api/submit-answer", json=answer_request)

        assert response.status_code == 404


class TestGetSubmissionEndpoint:
    """Tests for /api/submission/{id} endpoint."""

    def test_get_existing_submission(self):
        """Should retrieve existing submissions."""
        # Create submission
        code_request = {
            "code": "x = 5\ny = x * 2",
            "max_questions": 5
        }

        code_response = client.post("/api/submit-code", json=code_request)
        submission_id = code_response.json()["submission_id"]

        # Retrieve submission
        get_response = client.get(f"/api/submission/{submission_id}")

        assert get_response.status_code == 200
        data = get_response.json()

        assert data["submission_id"] == submission_id
        assert "questions" in data
        assert "metadata" in data

    def test_get_nonexistent_submission(self):
        """Should return 404 for nonexistent submissions."""
        response = client.get("/api/submission/sub_nonexistent")

        assert response.status_code == 404


class TestListTemplatesEndpoint:
    """Tests for /api/templates endpoint."""

    def test_list_templates(self):
        """Should list all available templates."""
        response = client.get("/api/templates")

        assert response.status_code == 200
        data = response.json()

        assert "templates" in data
        assert "total" in data
        assert len(data["templates"]) > 0

        # Check template structure
        template = data["templates"][0]
        assert "id" in template
        assert "name" in template
        assert "description" in template


class TestAPIIntegration:
    """Integration tests for complete workflow."""

    def test_complete_workflow(self):
        """Test complete workflow: submit -> get questions -> answer."""
        # Step 1: Submit code
        code_request = {
            "code": """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
""",
            "max_questions": 10,
            "strategy": "diverse"
        }

        submit_response = client.post("/api/submit-code", json=code_request)
        assert submit_response.status_code == 201

        submit_data = submit_response.json()
        submission_id = submit_data["submission_id"]

        # Step 2: Retrieve submission
        get_response = client.get(f"/api/submission/{submission_id}")
        assert get_response.status_code == 200

        get_data = get_response.json()
        assert get_data["submission_id"] == submission_id

        # Step 3: Submit answer (if questions exist)
        if len(submit_data["questions"]) > 0:
            question = submit_data["questions"][0]

            answer_request = {
                "submission_id": submission_id,
                "question_id": question["id"],
                "answer": question["correct_answer"]
            }

            answer_response = client.post("/api/submit-answer", json=answer_request)
            assert answer_response.status_code == 200

            answer_data = answer_response.json()
            assert answer_data["submission_id"] == submission_id

    def test_response_headers(self):
        """Should include custom headers."""
        response = client.get("/api/health")

        # Should have process time header
        assert "x-process-time" in response.headers


class TestValidation:
    """Tests for request validation."""

    def test_max_questions_validation(self):
        """Should validate max_questions bounds."""
        # Too high
        request_data = {
            "code": "x = 5",
            "max_questions": 100  # Over limit of 50
        }

        response = client.post("/api/submit-code", json=request_data)
        assert response.status_code == 422

        # Negative
        request_data["max_questions"] = -1
        response = client.post("/api/submit-code", json=request_data)
        assert response.status_code == 422

    def test_code_length_validation(self):
        """Should validate code length."""
        # Empty code
        request_data = {
            "code": "",
            "max_questions": 5
        }

        response = client.post("/api/submit-code", json=request_data)
        assert response.status_code == 422
