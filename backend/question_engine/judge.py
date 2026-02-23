"""
LLM-as-a-Judge Evaluator

Uses a second LLM to evaluate the quality of AI-generated comprehension questions.
Scores each question on 5 pedagogical dimensions and flags low-quality questions.

Based on the QLC LLM_JUDGE_PRD specification.
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from openai import OpenAI, APIError, RateLimitError, APIConnectionError

logger = logging.getLogger(__name__)


JUDGE_SYSTEM_PROMPT = """You are a quality evaluator for AI-generated comprehension questions about student code.

You have access to:
1. The student's original Python code
2. Static analysis results (ground truth about code structure)
3. Dynamic analysis results (ground truth about runtime values and behavior)
4. A generated question with its stated correct answer

Your task: score this question on 5 dimensions (1-5 each) and identify any issues.

CRITICAL RULES:
- For ACCURACY: cross-check the correct_answer against dynamic analysis values.
  If the question claims a variable equals X but dynamic analysis shows Y, accuracy = 1.
- For CODE_SPECIFICITY: could this exact question (with this exact answer) be asked
  about any Python program, or does it require knowing THIS specific code?
- Be strict. A score of 5 means the question is genuinely excellent on that dimension.
- A score of 3 is average/acceptable. Below 3 means there is a real problem.

Return JSON with this exact structure:
{
  "scores": {
    "accuracy": <1-5>,
    "clarity": <1-5>,
    "pedagogical_value": <1-5>,
    "code_specificity": <1-5>,
    "difficulty_calibration": <1-5>
  },
  "explanation": "<one paragraph explaining your scoring>",
  "issues": ["<issue 1>", "<issue 2>"]
}

The "issues" list should be empty if no significant problems were found.
"""


@dataclass
class JudgeConfig:
    """Configuration for the LLM judge."""
    model: str = "gpt-4o"
    temperature: float = 0.2
    max_tokens: int = 1000
    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class QuestionEvaluation:
    """Evaluation result for a single question."""
    question_id: str
    question_text: str
    scores: Dict[str, int]          # dimension -> 1-5
    overall_score: float
    explanation: str
    issues: List[str]
    is_flagged: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "question_text": self.question_text,
            "scores": self.scores,
            "overall_score": self.overall_score,
            "explanation": self.explanation,
            "issues": self.issues,
            "is_flagged": self.is_flagged,
        }


@dataclass
class EvaluationResult:
    """Complete evaluation result for all questions in a submission."""
    submission_id: str
    question_evaluations: List[QuestionEvaluation]
    aggregate: Dict[str, Any]
    tokens_used: int
    evaluation_time_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "submission_id": self.submission_id,
            "question_evaluations": [e.to_dict() for e in self.question_evaluations],
            "aggregate": self.aggregate,
            "tokens_used": self.tokens_used,
            "evaluation_time_ms": self.evaluation_time_ms,
        }


class LLMJudge:
    """
    LLM-as-a-Judge evaluator for generated comprehension questions.

    Makes one API call per question to focus the judge's attention and
    avoid cross-question influence.
    """

    def __init__(self, config: Optional[JudgeConfig] = None, api_key: Optional[str] = None):
        self.config = config or JudgeConfig()
        self.client = OpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
            timeout=self.config.request_timeout,
        )

    def evaluate_submission(self, submission_data: dict) -> EvaluationResult:
        """
        Evaluate all questions in a submission.

        Args:
            submission_data: Dict with keys: 'code', 'questions', 'result'
                            (as stored in submissions_store)

        Returns:
            EvaluationResult with per-question evaluations and aggregate stats
        """
        start_time = time.time()
        total_tokens = 0

        code = submission_data.get("code", "")
        questions = submission_data.get("questions", [])
        result = submission_data.get("result")

        static_analysis = getattr(result, "static_analysis", None) if result else None
        dynamic_analysis = getattr(result, "dynamic_analysis", None) if result else None

        evaluations: List[QuestionEvaluation] = []

        for question in questions:
            try:
                evaluation, tokens = self._evaluate_question(
                    question=question,
                    code=code,
                    static_analysis=static_analysis or {},
                    dynamic_analysis=dynamic_analysis or {},
                )
                evaluations.append(evaluation)
                total_tokens += tokens
            except Exception as e:
                logger.warning(f"Failed to evaluate question {getattr(question, 'id', '?')}: {e}")
                # Create a fallback evaluation for failed questions
                q_id = getattr(question, 'id', f"q_unknown_{len(evaluations)}")
                q_text = getattr(question, 'question_text', "Unknown question")
                evaluations.append(QuestionEvaluation(
                    question_id=q_id,
                    question_text=q_text,
                    scores={"accuracy": 0, "clarity": 0, "pedagogical_value": 0,
                            "code_specificity": 0, "difficulty_calibration": 0},
                    overall_score=0.0,
                    explanation=f"Evaluation failed: {str(e)}",
                    issues=["evaluation_error"],
                    is_flagged=True,
                ))

        aggregate = self._compute_aggregate(evaluations)
        elapsed_ms = (time.time() - start_time) * 1000

        return EvaluationResult(
            submission_id=submission_data.get("submission_id", "unknown"),
            question_evaluations=evaluations,
            aggregate=aggregate,
            tokens_used=total_tokens,
            evaluation_time_ms=elapsed_ms,
        )

    def _evaluate_question(
        self,
        question: Any,
        code: str,
        static_analysis: Dict[str, Any],
        dynamic_analysis: Dict[str, Any],
    ) -> Tuple[QuestionEvaluation, int]:
        """
        Evaluate a single question with retry logic.

        Returns:
            Tuple of (QuestionEvaluation, tokens_used)
        """
        q_id = getattr(question, 'id', 'unknown')
        q_text = getattr(question, 'question_text', '')

        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                prompt = self._build_judge_prompt(question, code, static_analysis, dynamic_analysis)

                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.config.temperature,
                    max_completion_tokens=self.config.max_tokens,
                    response_format={"type": "json_object"},
                )

                tokens_used = response.usage.total_tokens if response.usage else 0
                response_text = response.choices[0].message.content

                evaluation = self._parse_evaluation(response_text, q_id, q_text)
                return evaluation, tokens_used

            except RateLimitError as e:
                last_error = e
                wait_time = self.config.retry_delay * (2 ** attempt)
                logger.warning(f"Rate limited evaluating {q_id}, waiting {wait_time}s")
                time.sleep(wait_time)
            except (APIConnectionError, APIError) as e:
                last_error = e
                logger.warning(f"API error evaluating {q_id}, attempt {attempt + 1}: {e}")
                time.sleep(self.config.retry_delay)
            except json.JSONDecodeError as e:
                last_error = e
                logger.warning(f"JSON parse error for {q_id}, attempt {attempt + 1}: {e}")
                time.sleep(self.config.retry_delay)

        raise last_error or Exception(f"Failed to evaluate question {q_id} after all retries")

    def _build_judge_prompt(
        self,
        question: Any,
        code: str,
        static_analysis: Dict[str, Any],
        dynamic_analysis: Dict[str, Any],
    ) -> str:
        """Build the judge prompt for a single question."""
        q_text = getattr(question, 'question_text', '')
        correct_answer = getattr(question, 'correct_answer', '')
        question_type = getattr(question, 'question_type', '')
        question_level = getattr(question, 'question_level', '')
        difficulty = getattr(question, 'difficulty', 'medium')
        answer_choices = getattr(question, 'answer_choices', [])

        # Format answer choices if present
        choices_text = ""
        if answer_choices:
            choices_lines = []
            for c in answer_choices:
                correct_marker = "[CORRECT]" if getattr(c, 'is_correct', False) else ""
                choices_lines.append(f"  - {getattr(c, 'text', '')} {correct_marker}")
            choices_text = "\nAnswer Choices:\n" + "\n".join(choices_lines)

        # Compact analysis data (avoid token overload)
        static_compact = self._compact_static(static_analysis)
        dynamic_compact = self._compact_dynamic(dynamic_analysis)

        return f"""## Python Code
```python
{code}
```

## Static Analysis Summary
{json.dumps(static_compact, indent=2, default=str)}

## Dynamic Analysis Summary (Runtime Ground Truth)
{json.dumps(dynamic_compact, indent=2, default=str)}

## Question to Evaluate
- Question Text: {q_text}
- Question Type: {question_type}
- Question Level: {question_level}
- Difficulty Label: {difficulty}
- Stated Correct Answer: {correct_answer}{choices_text}

Evaluate this question on all 5 dimensions and return JSON as specified.
"""

    def _compact_static(self, static_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Keep only key static analysis fields to save tokens."""
        if not static_analysis:
            return {}
        return {
            "summary": static_analysis.get("summary", {}),
            "functions": [
                {"name": f.get("name"), "is_recursive": f.get("is_recursive"), "params": f.get("params", [])}
                for f in static_analysis.get("functions", [])[:10]
            ],
            "loops": [
                {"type": l.get("type"), "line_start": l.get("line_start")}
                for l in static_analysis.get("loops", [])[:10]
            ],
            "variables": [
                {"name": v.get("name"), "scope": v.get("scope")}
                for v in static_analysis.get("variables", [])[:15]
            ],
        }

    def _compact_dynamic(self, dynamic_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Keep only key dynamic analysis fields to save tokens."""
        if not dynamic_analysis:
            return {}
        return {
            "execution_successful": dynamic_analysis.get("execution_successful"),
            "final_variables": dynamic_analysis.get("final_variables", {}),
            "function_calls": [
                {"function_name": c.get("function_name"), "return_value": c.get("return_value")}
                for c in dynamic_analysis.get("function_calls", [])[:10]
            ],
            "loop_executions": dynamic_analysis.get("loop_executions", [])[:10],
            "stdout": str(dynamic_analysis.get("stdout", ""))[:300],
            "has_recursion": dynamic_analysis.get("has_recursion"),
            "max_stack_depth": dynamic_analysis.get("max_stack_depth"),
        }

    def _parse_evaluation(
        self,
        response_text: str,
        question_id: str,
        question_text: str,
    ) -> QuestionEvaluation:
        """Parse the judge's JSON response into a QuestionEvaluation."""
        data = json.loads(response_text)

        scores = data.get("scores", {})

        # Validate and clamp scores to 1-5
        validated_scores = {}
        for dim in ["accuracy", "clarity", "pedagogical_value", "code_specificity", "difficulty_calibration"]:
            raw = scores.get(dim, 3)
            validated_scores[dim] = max(1, min(5, int(raw)))

        # Compute overall score: accuracy and pedagogical_value weighted 2x
        a = validated_scores["accuracy"]
        c = validated_scores["clarity"]
        p = validated_scores["pedagogical_value"]
        s = validated_scores["code_specificity"]
        d = validated_scores["difficulty_calibration"]
        overall = (a * 2 + c + p * 2 + s + d) / 7.0

        explanation = str(data.get("explanation", ""))
        issues = [str(i) for i in data.get("issues", [])]

        is_flagged = overall < 3.0 or validated_scores["accuracy"] < 3

        return QuestionEvaluation(
            question_id=question_id,
            question_text=question_text,
            scores=validated_scores,
            overall_score=round(overall, 2),
            explanation=explanation,
            issues=issues,
            is_flagged=is_flagged,
        )

    def _compute_aggregate(self, evaluations: List[QuestionEvaluation]) -> Dict[str, Any]:
        """Compute aggregate statistics across all question evaluations."""
        if not evaluations:
            return {
                "mean_overall": 0.0,
                "mean_accuracy": 0.0,
                "mean_clarity": 0.0,
                "mean_pedagogical_value": 0.0,
                "mean_code_specificity": 0.0,
                "mean_difficulty_calibration": 0.0,
                "total_questions": 0,
                "questions_flagged": 0,
                "questions_flagged_ids": [],
            }

        valid = [e for e in evaluations if e.overall_score > 0]
        n = len(valid)

        def mean_dim(dim: str) -> float:
            if not valid:
                return 0.0
            return round(sum(e.scores.get(dim, 0) for e in valid) / n, 2)

        flagged = [e for e in evaluations if e.is_flagged]

        return {
            "mean_overall": round(sum(e.overall_score for e in valid) / n, 2) if n > 0 else 0.0,
            "mean_accuracy": mean_dim("accuracy"),
            "mean_clarity": mean_dim("clarity"),
            "mean_pedagogical_value": mean_dim("pedagogical_value"),
            "mean_code_specificity": mean_dim("code_specificity"),
            "mean_difficulty_calibration": mean_dim("difficulty_calibration"),
            "total_questions": len(evaluations),
            "questions_flagged": len(flagged),
            "questions_flagged_ids": [e.question_id for e in flagged],
        }
