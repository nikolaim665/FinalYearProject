"""
Question Agent Node

Generates question TEXT ONLY (no answers/distractors) using the static and
dynamic analysis results plus optional RAG context.
"""

import json
import logging
import time
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from question_engine.state import QLCState

logger = logging.getLogger(__name__)

QUESTION_SYSTEM_PROMPT = """You are an expert computer science educator specialising in assessing student
understanding of their own code.

You will receive:
1. The student's Python code
2. Static analysis results (code structure)
3. Dynamic analysis results (runtime behaviour)
4. (Optional) Relevant lecture material context

Generate ONLY the question text and metadata. Do NOT generate answers.

For each question, output a JSON object with:
- question_text: The question to ask the student
- question_type: "multiple_choice" (always, for this pipeline)
- question_level: "atom" | "block" | "relational" | "macro"
- difficulty: "easy" | "medium" | "hard"
- context: { "line_number": int|null, "variable_name": str|null, "function_name": str|null, "data_type": str|null, "loop_type": str|null }
- template_id: "ai_generated_<level>"

Question Levels (Block Model):
- ATOM: Basic language elements (variable values, types, operators)
- BLOCK: Code sections (loop iterations, function returns, conditional branches)
- RELATIONAL: Connections between parts (how function A uses result of B)
- MACRO: Whole program understanding (purpose, algorithm, complexity)

Rules:
- Questions must be answerable from the analysis data provided
- Cover diverse levels and difficulties
- Make questions specific to THIS code, not generic Python trivia
- If lecture context is provided, align questions with taught concepts
- Return ONLY valid JSON: {"questions": [...]}
- Do not include answers or answer choices — those come from the Answer Agent"""


def _compact_analysis(static: Optional[dict], dynamic: Optional[dict]) -> str:
    """Return a compact JSON representation to keep prompts short."""
    out: dict = {}
    if static:
        summary = static.get("summary", {})
        functions = static.get("functions", [])[:10]
        loops = static.get("loops", [])[:10]
        variables = static.get("variables", [])[:15]
        out["static"] = {
            "summary": summary,
            "functions": [
                {k: v for k, v in fn.items() if k in
                 ("name", "params", "is_recursive", "complexity", "line_start")}
                for fn in functions
            ],
            "loops": [
                {k: v for k, v in lp.items() if k in ("loop_type", "line", "nesting")}
                for lp in loops
            ],
            "variables": [
                {k: v for k, v in vr.items() if k in ("name", "scope", "type_annotation")}
                for vr in variables
            ],
        }
    if dynamic:
        out["dynamic"] = {
            "execution_successful": dynamic.get("execution_successful"),
            "final_variables": dict(list(dynamic.get("final_variables", {}).items())[:10]),
            "function_calls": dynamic.get("function_calls", [])[:10],
            "loop_executions": dynamic.get("loop_executions", {}),
        }
    return json.dumps(out, default=str)


def question_agent_node(state: QLCState) -> dict:
    """
    LangGraph node: Generate question text (no answers).

    Updates state with:
    - questions: list of question dicts (text + metadata only)
    - tokens_used (incremented)
    """
    start = time.time()
    config: dict = state.get("config", {})
    model: str = config.get("question_model", "gpt-4o")
    max_q: int = state.get("max_questions", 10)
    source_code: str = state["source_code"]
    static_analysis: Optional[dict] = state.get("static_analysis")
    dynamic_analysis: Optional[dict] = state.get("dynamic_analysis")
    rag_context: Optional[str] = state.get("rag_context")

    allowed_levels: list = config.get("include_levels", [])
    allowed_types: list = config.get("include_types", [])
    allowed_difficulties: list = config.get("include_difficulties", [])

    # Build user message
    analysis_text = _compact_analysis(static_analysis, dynamic_analysis)

    rag_section = ""
    if rag_context:
        rag_section = f"\n\n## Relevant Lecture Material\n{rag_context}"

    level_filter = ""
    if allowed_levels:
        level_filter = f"\nOnly generate questions at these levels: {', '.join(allowed_levels)}."
    difficulty_filter = ""
    if allowed_difficulties:
        difficulty_filter = f"\nOnly use these difficulties: {', '.join(allowed_difficulties)}."

    user_content = f"""Generate up to {max_q} multiple-choice comprehension questions about the following Python code.{level_filter}{difficulty_filter}

## Student's Code
```python
{source_code}
```

## Analysis Data
```json
{analysis_text}
```{rag_section}

Return a JSON object with a "questions" array. Each element must match the schema described in the system prompt."""

    llm = ChatOpenAI(model=model, temperature=0.7)

    tokens_used = state.get("tokens_used", 0)
    questions: list[dict] = []

    try:
        response = llm.invoke([
            SystemMessage(content=QUESTION_SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ])

        # Track tokens if usage metadata is available
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            tokens_used += response.usage_metadata.get("total_tokens", 0)

        raw = response.content.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        parsed = json.loads(raw)
        questions = parsed.get("questions", [])
        logger.info("Question agent generated %d questions", len(questions))

    except json.JSONDecodeError as e:
        logger.error("Question agent JSON parse error: %s", e)
    except Exception as e:
        logger.error("Question agent error: %s", e)

    elapsed = (time.time() - start) * 1000
    return {
        "questions": questions,
        "tokens_used": tokens_used,
        "execution_time_ms": state.get("execution_time_ms", 0.0) + elapsed,
    }
