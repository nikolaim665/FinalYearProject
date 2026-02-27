"""
Judge Agent Node (Background / Async)

Independently evaluates each generated question+answer set on 5 pedagogical
dimensions. Runs synchronously within the graph but its results are stored
for later retrieval via the /evaluate endpoint.
"""

import json
import logging
import time
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from question_engine.state import QLCState

logger = logging.getLogger(__name__)

JUDGE_SYSTEM_PROMPT = """You are an expert pedagogical evaluator for computer-science comprehension questions.

You will receive:
1. Python source code
2. Static analysis results
3. Dynamic analysis results
4. A generated multiple-choice question with its correct answer and distractors

Score the question on these 5 dimensions (integer 1-5):

- accuracy (weight 2x): Is the correct answer actually correct per the code/analysis data?
  1 = definitely wrong  5 = verifiably correct
- clarity (weight 1x): Is the question unambiguous and well-phrased?
  1 = very confusing  5 = crystal clear
- pedagogical_value (weight 2x): Does this question identify genuine understanding gaps?
  1 = trivial / no insight  5 = excellent insight into understanding
- code_specificity (weight 1x): Must you know THIS code to answer, or is it generic Python trivia?
  1 = generic trivia  5 = requires reading this exact code
- difficulty_calibration (weight 1x): Does the stated difficulty match the actual cognitive demand?
  1 = completely wrong  5 = perfect match

Overall score formula: (accuracy*2 + clarity + pedagogical_value*2 + code_specificity + difficulty_calibration) / 7

Return ONLY valid JSON:
{
  "question_id": "<id>",
  "scores": {
    "accuracy": <int 1-5>,
    "clarity": <int 1-5>,
    "pedagogical_value": <int 1-5>,
    "code_specificity": <int 1-5>,
    "difficulty_calibration": <int 1-5>
  },
  "overall_score": <float, 2 decimal places>,
  "explanation": "<2-3 sentence reasoning>",
  "issues": ["<issue 1>", ...],
  "is_flagged": <bool: overall_score < 3.0 OR accuracy < 3>
}"""


def _compact_analysis(static: Optional[dict], dynamic: Optional[dict]) -> str:
    """Compact analysis for judge prompt."""
    out: dict = {}
    if static:
        out["static"] = {
            "summary": static.get("summary", {}),
            "functions": [
                {k: v for k, v in fn.items() if k in ("name", "is_recursive", "complexity")}
                for fn in static.get("functions", [])[:5]
            ],
        }
    if dynamic:
        out["dynamic"] = {
            "execution_successful": dynamic.get("execution_successful"),
            "final_variables": dict(list(dynamic.get("final_variables", {}).items())[:10]),
            "function_calls": dynamic.get("function_calls", [])[:5],
        }
    return json.dumps(out, default=str)


def judge_agent_node(state: QLCState) -> dict:
    """
    LangGraph node: Evaluate question quality.

    Scores all questions in questions_complete on 5 pedagogical dimensions.
    Updates state.evaluation with aggregate and per-question scores.
    """
    start = time.time()
    config: dict = state.get("config", {})
    model: str = config.get("judge_model", "gpt-4o")
    source_code: str = state["source_code"]
    questions_complete: list[dict] = state.get("questions_complete", [])
    static_analysis: Optional[dict] = state.get("static_analysis")
    dynamic_analysis: Optional[dict] = state.get("dynamic_analysis")

    tokens_used = state.get("tokens_used", 0)

    if not questions_complete:
        return {"evaluation": None, "tokens_used": tokens_used}

    analysis_text = _compact_analysis(static_analysis, dynamic_analysis)
    llm = ChatOpenAI(model=model, temperature=0.1)

    question_evaluations = []
    for i, question in enumerate(questions_complete):
        q_id = question.get("id", f"q_{i}")
        q_text = question.get("question_text", "")
        correct = question.get("correct_answer", "")
        choices = question.get("answer_choices", [])
        difficulty = question.get("difficulty", "medium")
        level = question.get("question_level", "block")

        choices_text = "\n".join(
            f"  {'✓' if c.get('is_correct') else '✗'} {c.get('text', '')}"
            for c in choices
        )

        user_content = f"""Evaluate this question about the following Python code.

## Source Code
```python
{source_code}
```

## Analysis Data
```json
{analysis_text}
```

## Question to Evaluate
ID: {q_id}
Level: {level}
Difficulty: {difficulty}
Question: {q_text}
Answer choices:
{choices_text}
Correct answer: {correct}

Return your evaluation as JSON."""

        try:
            response = llm.invoke([
                SystemMessage(content=JUDGE_SYSTEM_PROMPT),
                HumanMessage(content=user_content),
            ])

            if hasattr(response, "usage_metadata") and response.usage_metadata:
                tokens_used += response.usage_metadata.get("total_tokens", 0)

            raw = response.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            eval_data = json.loads(raw)
            # Ensure question_id is set
            eval_data["question_id"] = q_id
            eval_data["question_text"] = q_text

            # Clamp scores to 1-5
            scores = eval_data.get("scores", {})
            for dim in ("accuracy", "clarity", "pedagogical_value", "code_specificity", "difficulty_calibration"):
                if dim in scores:
                    scores[dim] = max(1, min(5, int(scores[dim])))

            # Recompute overall_score
            s = scores
            denom = 7
            numerator = (
                s.get("accuracy", 3) * 2
                + s.get("clarity", 3)
                + s.get("pedagogical_value", 3) * 2
                + s.get("code_specificity", 3)
                + s.get("difficulty_calibration", 3)
            )
            overall = round(numerator / denom, 2)
            eval_data["overall_score"] = overall
            eval_data["is_flagged"] = overall < 3.0 or s.get("accuracy", 3) < 3

            question_evaluations.append(eval_data)

        except Exception as e:
            logger.error("Judge agent failed for question %s: %s", q_id, e)
            question_evaluations.append({
                "question_id": q_id,
                "question_text": q_text,
                "scores": {},
                "overall_score": 0.0,
                "explanation": f"Evaluation failed: {e}",
                "issues": [str(e)],
                "is_flagged": True,
            })

    # Compute aggregate
    valid_evals = [e for e in question_evaluations if e.get("scores")]
    aggregate: dict = {"total_questions": len(questions_complete), "questions_flagged": 0}

    if valid_evals:
        dims = ("accuracy", "clarity", "pedagogical_value", "code_specificity", "difficulty_calibration")
        for dim in dims:
            values = [e["scores"].get(dim, 0) for e in valid_evals if e.get("scores")]
            aggregate[f"mean_{dim}"] = round(sum(values) / len(values), 2) if values else 0.0
        overalls = [e.get("overall_score", 0) for e in valid_evals]
        aggregate["mean_overall"] = round(sum(overalls) / len(overalls), 2) if overalls else 0.0
        flagged = [e for e in question_evaluations if e.get("is_flagged")]
        aggregate["questions_flagged"] = len(flagged)
        aggregate["questions_flagged_ids"] = [e.get("question_id") for e in flagged]

    evaluation = {
        "question_evaluations": question_evaluations,
        "aggregate": aggregate,
        "tokens_used": tokens_used,
        "evaluation_time_ms": (time.time() - start) * 1000,
    }

    elapsed = (time.time() - start) * 1000
    return {
        "evaluation": evaluation,
        "tokens_used": tokens_used,
        "execution_time_ms": state.get("execution_time_ms", 0.0) + elapsed,
    }
