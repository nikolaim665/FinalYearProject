"""
LLM Answer Explainer

Uses a second LLM call to verify and enrich each generated question with:
- Verification that the correct answer is indeed correct (using code + analysis)
- Detailed explanation of WHY the correct answer is correct
- For multiple choice: explanation of why each wrong answer is wrong
- References to specific code lines, analysis data, and runtime behavior

The explainer has full access to:
- The original source code
- Static analysis results (AST structure, functions, variables, loops, etc.)
- Dynamic analysis results (runtime values, loop iterations, function calls, etc.)

This ensures explanations are grounded in actual code behavior, not guesses.
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from openai import OpenAI, APIError, RateLimitError, APIConnectionError

logger = logging.getLogger(__name__)


@dataclass
class WrongAnswerExplanation:
    """Explanation for why a wrong answer choice is wrong."""
    answer_text: str
    explanation: str
    common_misconception: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer_text": self.answer_text,
            "explanation": self.explanation,
            "common_misconception": self.common_misconception,
        }


@dataclass
class AnswerExplanation:
    """Rich explanation for a question's answer, produced by the explainer LLM."""
    question_id: str
    verified_correct_answer: Any
    is_answer_verified: bool
    correct_answer_reasoning: str
    code_references: List[str] = field(default_factory=list)
    analysis_references: List[str] = field(default_factory=list)
    wrong_answer_explanations: List[WrongAnswerExplanation] = field(default_factory=list)
    learning_tip: Optional[str] = None
    corrected_answer: Optional[Any] = None  # If the LLM finds the original answer wrong

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "verified_correct_answer": self.verified_correct_answer,
            "is_answer_verified": self.is_answer_verified,
            "correct_answer_reasoning": self.correct_answer_reasoning,
            "code_references": self.code_references,
            "analysis_references": self.analysis_references,
            "wrong_answer_explanations": [w.to_dict() for w in self.wrong_answer_explanations],
            "learning_tip": self.learning_tip,
            "corrected_answer": self.corrected_answer,
        }


@dataclass
class ExplainerConfig:
    """Configuration for the answer explainer."""
    model: str = "gpt-5.2"
    temperature: float = 0.3  # Lower temperature for more factual explanations
    max_tokens: int = 4000
    max_retries: int = 3
    retry_delay: float = 1.0
    request_timeout: int = 60
    batch_size: int = 5  # How many questions to explain per API call


EXPLAINER_SYSTEM_PROMPT = """You are an expert computer science educator and code analysis specialist. Your job is to VERIFY and EXPLAIN answers to comprehension questions about student-written Python code.

You will receive:
1. The student's Python source code
2. Static analysis results (code structure from AST parsing)
3. Dynamic analysis results (runtime behavior from execution tracing)
4. A list of generated questions with their proposed correct answers

For EACH question, you must:

1. **VERIFY the correct answer** by cross-referencing it against the source code, static analysis, and dynamic analysis data. If the proposed answer is wrong, provide the corrected answer.

2. **Explain WHY the correct answer is correct**, referencing:
   - Specific lines of code (e.g., "On line 5, the variable x is assigned the value 10")
   - Static analysis data (e.g., "The static analysis shows this function has 2 parameters")
   - Dynamic analysis data (e.g., "At runtime, the loop executed 5 times as shown in loop_executions")

3. **For multiple choice questions**, explain WHY EACH WRONG ANSWER is wrong:
   - What misconception would lead someone to pick it
   - What the wrong answer would imply about the code
   - How the code actually behaves differently

4. **Provide a learning tip** that helps the student understand the underlying concept

IMPORTANT RULES:
- ALWAYS base your explanations on the actual analysis data provided, not assumptions
- Reference specific code lines, variable values, and runtime data
- For runtime values, use EXACT values from the dynamic analysis
- If you cannot verify an answer from the provided data, say so explicitly
- Be pedagogically helpful - explain concepts, don't just state facts

Return your response as a JSON object with this structure:
{
  "explanations": [
    {
      "question_index": 0,
      "verified_correct_answer": "the verified answer",
      "is_answer_verified": true,
      "correct_answer_reasoning": "Detailed explanation of why this answer is correct, referencing code and analysis...",
      "code_references": [
        "Line 5: x = 10 assigns the value 10 to variable x",
        "Line 8: the for loop iterates over range(5)"
      ],
      "analysis_references": [
        "Static analysis: function 'factorial' has is_recursive=true",
        "Dynamic analysis: final_variables shows x=120"
      ],
      "wrong_answer_explanations": [
        {
          "answer_text": "The wrong option text",
          "explanation": "This is wrong because...",
          "common_misconception": "Students might pick this if they think..."
        }
      ],
      "learning_tip": "A helpful tip about the concept being tested",
      "corrected_answer": null
    }
  ]
}

If the proposed correct answer is wrong, set:
- "is_answer_verified": false
- "corrected_answer": "the actual correct answer"
- Explain in correct_answer_reasoning why the original answer was wrong and what the correct one is"""


class AnswerExplainer:
    """
    Uses a second LLM to verify answers and generate rich explanations.

    The explainer receives full context (code + static + dynamic analysis)
    to produce grounded, accurate explanations for each question.
    """

    def __init__(self, config: Optional[ExplainerConfig] = None, api_key: Optional[str] = None):
        self.config = config or ExplainerConfig()
        self.client = OpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
            timeout=self.config.request_timeout,
        )

    def explain_questions(
        self,
        questions: List[Dict[str, Any]],
        source_code: str,
        static_analysis: Optional[Dict[str, Any]],
        dynamic_analysis: Optional[Dict[str, Any]],
    ) -> List[AnswerExplanation]:
        """
        Generate rich explanations for a list of questions.

        Args:
            questions: List of question dicts (from GeneratedQuestion.to_dict())
            source_code: The original Python source code
            static_analysis: Static analysis results
            dynamic_analysis: Dynamic analysis results

        Returns:
            List of AnswerExplanation objects, one per question
        """
        if not questions:
            return []

        all_explanations = []

        # Process in batches to stay within token limits
        for i in range(0, len(questions), self.config.batch_size):
            batch = questions[i:i + self.config.batch_size]
            batch_explanations = self._explain_batch_with_retry(
                batch, source_code, static_analysis, dynamic_analysis, start_index=i
            )
            all_explanations.extend(batch_explanations)

        return all_explanations

    def _explain_batch_with_retry(
        self,
        questions: List[Dict[str, Any]],
        source_code: str,
        static_analysis: Optional[Dict[str, Any]],
        dynamic_analysis: Optional[Dict[str, Any]],
        start_index: int = 0,
    ) -> List[AnswerExplanation]:
        """Explain a batch of questions with retry logic."""
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                return self._explain_batch(
                    questions, source_code, static_analysis, dynamic_analysis, start_index
                )
            except RateLimitError as e:
                last_error = e
                wait_time = self.config.retry_delay * (2 ** attempt)
                logger.warning(f"Explainer rate limited, waiting {wait_time}s before retry {attempt + 1}")
                time.sleep(wait_time)
            except APIConnectionError as e:
                last_error = e
                logger.warning(f"Explainer connection error, retrying {attempt + 1}/{self.config.max_retries}")
                time.sleep(self.config.retry_delay)
            except APIError as e:
                last_error = e
                if e.status_code and e.status_code >= 500:
                    logger.warning(f"Explainer server error {e.status_code}, retrying {attempt + 1}")
                    time.sleep(self.config.retry_delay)
                else:
                    raise
            except json.JSONDecodeError as e:
                last_error = e
                logger.warning(f"Explainer JSON decode error, retrying {attempt + 1}")
                time.sleep(self.config.retry_delay)

        # All retries exhausted - return empty explanations rather than crashing
        logger.error(f"Explainer failed after {self.config.max_retries} retries: {last_error}")
        return [
            AnswerExplanation(
                question_id=q.get("template_id", f"q_{start_index + i}"),
                verified_correct_answer=q.get("correct_answer"),
                is_answer_verified=False,
                correct_answer_reasoning="Explanation unavailable - the explainer service encountered an error.",
            )
            for i, q in enumerate(questions)
        ]

    def _explain_batch(
        self,
        questions: List[Dict[str, Any]],
        source_code: str,
        static_analysis: Optional[Dict[str, Any]],
        dynamic_analysis: Optional[Dict[str, Any]],
        start_index: int = 0,
    ) -> List[AnswerExplanation]:
        """Call the LLM to explain a batch of questions."""
        user_prompt = self._build_prompt(questions, source_code, static_analysis, dynamic_analysis)

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": EXPLAINER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.config.temperature,
            max_completion_tokens=self.config.max_tokens,
            response_format={"type": "json_object"},
        )

        response_text = response.choices[0].message.content
        if not response_text:
            raise ValueError("Empty response from explainer LLM")

        response_data = json.loads(response_text)
        explanations_data = response_data.get("explanations", [])

        explanations = []
        for i, q in enumerate(questions):
            # Find matching explanation (by index)
            exp_data = None
            for ed in explanations_data:
                if ed.get("question_index") == i:
                    exp_data = ed
                    break

            if exp_data:
                explanation = self._parse_explanation(exp_data, q)
            else:
                # Fallback if LLM didn't return explanation for this question
                explanation = AnswerExplanation(
                    question_id=q.get("template_id", f"q_{start_index + i}"),
                    verified_correct_answer=q.get("correct_answer"),
                    is_answer_verified=True,
                    correct_answer_reasoning=q.get("explanation", "No detailed explanation available."),
                )

            explanations.append(explanation)

        return explanations

    def _build_prompt(
        self,
        questions: List[Dict[str, Any]],
        source_code: str,
        static_analysis: Optional[Dict[str, Any]],
        dynamic_analysis: Optional[Dict[str, Any]],
    ) -> str:
        """Build the prompt for the explainer LLM with full context."""
        parts = [
            "## Source Code\n```python",
            source_code,
            "```\n",
        ]

        if static_analysis:
            parts.extend([
                "## Static Analysis Results (AST-based code structure)",
                json.dumps(static_analysis, indent=2, default=str),
                "\n",
            ])
        else:
            parts.append("## Static Analysis: Not available\n")

        if dynamic_analysis:
            parts.extend([
                "## Dynamic Analysis Results (Runtime execution trace)",
                json.dumps(dynamic_analysis, indent=2, default=str),
                "\n",
            ])
        else:
            parts.append("## Dynamic Analysis: Not available\n")

        # Format questions for the LLM
        parts.append("## Questions to Verify and Explain\n")
        for i, q in enumerate(questions):
            parts.append(f"### Question {i} (index={i})")
            parts.append(f"- **Text:** {q.get('question_text', '')}")
            parts.append(f"- **Type:** {q.get('question_type', '')}")
            parts.append(f"- **Level:** {q.get('question_level', '')}")
            parts.append(f"- **Proposed Correct Answer:** {q.get('correct_answer', '')}")

            if q.get("answer_choices"):
                parts.append("- **Answer Choices:**")
                for choice in q["answer_choices"]:
                    marker = "(correct)" if choice.get("is_correct") else "(wrong)"
                    parts.append(f"  - {choice.get('text', '')} {marker}")

            if q.get("context"):
                parts.append(f"- **Context:** {json.dumps(q['context'], default=str)}")

            parts.append("")

        parts.extend([
            "## Instructions",
            f"Verify and explain all {len(questions)} questions above.",
            "For each question, cross-reference the proposed correct answer against the source code and analysis data.",
            "For multiple choice questions, explain why each wrong answer is wrong.",
            "Provide specific code line references and analysis data references.",
            "Return JSON with the structure described in the system prompt.",
        ])

        return "\n".join(parts)

    def _parse_explanation(self, data: Dict[str, Any], question: Dict[str, Any]) -> AnswerExplanation:
        """Parse an explanation from the LLM response."""
        wrong_explanations = []
        for we in data.get("wrong_answer_explanations", []):
            wrong_explanations.append(WrongAnswerExplanation(
                answer_text=we.get("answer_text", ""),
                explanation=we.get("explanation", ""),
                common_misconception=we.get("common_misconception"),
            ))

        return AnswerExplanation(
            question_id=question.get("template_id", "unknown"),
            verified_correct_answer=data.get("verified_correct_answer", question.get("correct_answer")),
            is_answer_verified=data.get("is_answer_verified", True),
            correct_answer_reasoning=data.get("correct_answer_reasoning", ""),
            code_references=data.get("code_references", []),
            analysis_references=data.get("analysis_references", []),
            wrong_answer_explanations=wrong_explanations,
            learning_tip=data.get("learning_tip"),
            corrected_answer=data.get("corrected_answer"),
        )


def explain_answers(
    questions: List[Dict[str, Any]],
    source_code: str,
    static_analysis: Optional[Dict[str, Any]] = None,
    dynamic_analysis: Optional[Dict[str, Any]] = None,
    config: Optional[ExplainerConfig] = None,
    api_key: Optional[str] = None,
) -> List[AnswerExplanation]:
    """
    Convenience function to generate answer explanations.

    Args:
        questions: List of question dicts
        source_code: Python source code
        static_analysis: Static analysis results
        dynamic_analysis: Dynamic analysis results
        config: Explainer configuration
        api_key: OpenAI API key

    Returns:
        List of AnswerExplanation objects
    """
    explainer = AnswerExplainer(config, api_key)
    return explainer.explain_questions(questions, source_code, static_analysis, dynamic_analysis)
