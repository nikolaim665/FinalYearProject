"""
QLC State Schema for LangGraph Pipeline

Defines the central typed state that flows through all nodes in the
LangGraph StateGraph pipeline.
"""

from typing import TypedDict, Optional, List


class QLCState(TypedDict):
    """
    Central state object flowing through the LangGraph QLC pipeline.

    All fields that are populated later in the pipeline are Optional
    and initialized to None/empty by the caller before graph.invoke().
    """

    # --- Inputs ---
    source_code: str                     # Student's Python code
    lecture_slides: Optional[str]        # Raw text of lecture slides (if any)
    max_questions: int                   # How many questions to generate
    config: dict                         # GenerationConfig as dict

    # --- RAG ---
    rag_context: Optional[str]           # Retrieved lecture context (if any)

    # --- Analysis ---
    static_analysis: Optional[dict]      # Output of StaticAnalyzer.analyze()
    dynamic_analysis: Optional[dict]     # Output of DynamicAnalyzer.analyze()
    analysis_warnings: List[str]         # Non-fatal warnings
    analysis_errors: List[str]           # Fatal errors

    # --- Questions ---
    questions: List[dict]                # Question text + metadata (no answers yet)

    # --- Answers ---
    questions_with_answers: List[dict]   # Questions enriched with correct + 3 distractors

    # --- Explanations ---
    questions_complete: List[dict]       # Fully enriched with distractor explanations

    # --- Judge (async) ---
    evaluation: Optional[dict]           # Judge scores (populated asynchronously)

    # --- Metadata ---
    tokens_used: int
    execution_time_ms: float
    from_cache: bool


def make_initial_state(
    source_code: str,
    max_questions: int = 10,
    lecture_slides: Optional[str] = None,
    config: Optional[dict] = None,
) -> QLCState:
    """
    Create a fully-initialised QLCState dict with sensible defaults.

    Call this before graph.invoke() so every key is present and typed.
    """
    return QLCState(
        source_code=source_code,
        lecture_slides=lecture_slides,
        max_questions=max_questions,
        config=config or {},
        rag_context=None,
        static_analysis=None,
        dynamic_analysis=None,
        analysis_warnings=[],
        analysis_errors=[],
        questions=[],
        questions_with_answers=[],
        questions_complete=[],
        evaluation=None,
        tokens_used=0,
        execution_time_ms=0.0,
        from_cache=False,
    )
