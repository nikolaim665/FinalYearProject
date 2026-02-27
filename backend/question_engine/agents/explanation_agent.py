"""
Explanation Agent Node

For each distractor (wrong answer) in each question, generates a clear explanation
of WHY it is wrong and what misconception it reveals.
Also generates the explanation for the correct answer.
"""

import json
import logging
import time
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from question_engine.state import QLCState

logger = logging.getLogger(__name__)

EXPLANATION_SYSTEM_PROMPT = """You are a patient computer science tutor. For each multiple-choice question
about student Python code, write clear, encouraging explanations.

For each question you receive, produce:
1. A brief explanation of why the CORRECT answer is correct (referencing specific code behaviour)
2. For each WRONG answer (distractor): an explanation of why it is wrong and what misconception
   would lead a student to choose it, plus a brief learning tip

Keep explanations concise (2-3 sentences each). Use a supportive, educational tone.

Return ONLY valid JSON:
{
  "explanations": [
    {
      "question_index": 0,
      "correct_answer_explanation": "<explanation of correct answer>",
      "distractor_explanations": [
        {
          "distractor_text": "<text>",
          "why_wrong": "<explanation>",
          "learning_tip": "<tip>"
        }
      ]
    }
  ]
}"""


def explanation_agent_node(state: QLCState) -> dict:
    """
    LangGraph node: Generate explanations for all answer choices.

    Updates state with:
    - questions_complete: list of fully enriched question dicts
    - tokens_used (incremented)
    """
    start = time.time()
    config: dict = state.get("config", {})
    model: str = config.get("explanation_model", "gpt-4o-mini")
    source_code: str = state["source_code"]
    questions_with_answers: list[dict] = state.get("questions_with_answers", [])

    tokens_used = state.get("tokens_used", 0)

    if not questions_with_answers:
        logger.warning("Explanation agent received no questions to process")
        return {
            "questions_complete": [],
            "tokens_used": tokens_used,
        }

    # Build a compact representation for the explanation prompt
    questions_for_prompt = []
    for i, q in enumerate(questions_with_answers):
        questions_for_prompt.append({
            "index": i,
            "question_text": q.get("question_text", ""),
            "correct_answer": q.get("correct_answer", ""),
            "distractors": [
                c.get("text", "") for c in q.get("answer_choices", [])
                if not c.get("is_correct")
            ],
        })

    questions_json = json.dumps(questions_for_prompt, indent=2)

    user_content = f"""Generate explanations for the answer choices of these questions about this Python code.

## Student's Code
```python
{source_code}
```

## Questions with Answers
```json
{questions_json}
```

For each question, explain why the correct answer is correct and why each distractor is wrong.
Return JSON only."""

    llm = ChatOpenAI(model=model, temperature=0.3)
    explanations_by_index: dict = {}

    try:
        response = llm.invoke([
            SystemMessage(content=EXPLANATION_SYSTEM_PROMPT),
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

        parsed = json.loads(raw)
        for exp_item in parsed.get("explanations", []):
            idx = exp_item.get("question_index", -1)
            if idx >= 0:
                explanations_by_index[idx] = exp_item

        logger.info("Explanation agent generated %d explanations", len(explanations_by_index))

    except json.JSONDecodeError as e:
        logger.error("Explanation agent JSON parse error: %s", e)
    except Exception as e:
        logger.error("Explanation agent error: %s", e)

    # Merge explanations into questions
    questions_complete = []
    for i, question in enumerate(questions_with_answers):
        complete = dict(question)
        exp_data = explanations_by_index.get(i, {})

        # Set top-level explanation (for correct answer)
        complete["explanation"] = exp_data.get("correct_answer_explanation", "")

        # Map distractor explanations back to answer_choices
        distractor_explanations = {
            d.get("distractor_text", ""): d
            for d in exp_data.get("distractor_explanations", [])
        }

        updated_choices = []
        for choice in complete.get("answer_choices", []):
            choice_copy = dict(choice)
            if not choice_copy.get("is_correct"):
                d_text = choice_copy.get("text", "")
                d_exp = distractor_explanations.get(d_text, {})
                why_wrong = d_exp.get("why_wrong", "")
                learning_tip = d_exp.get("learning_tip", "")
                if why_wrong and learning_tip:
                    choice_copy["explanation"] = f"{why_wrong} Tip: {learning_tip}"
                elif why_wrong:
                    choice_copy["explanation"] = why_wrong
            else:
                # Correct answer explanation
                choice_copy["explanation"] = exp_data.get("correct_answer_explanation", "")

            updated_choices.append(choice_copy)

        complete["answer_choices"] = updated_choices
        questions_complete.append(complete)

    elapsed = (time.time() - start) * 1000
    return {
        "questions_complete": questions_complete,
        "tokens_used": tokens_used,
        "execution_time_ms": state.get("execution_time_ms", 0.0) + elapsed,
    }
