"""
LangGraph StateGraph Definition for the QLC Pipeline

Entry point: build_qlc_graph() -> CompiledGraph

Pipeline flow:
  [START]
    → rag_check (conditional)
      ├── lecture_slides present → rag_retrieve → analyzer_agent
      └── no slides → analyzer_agent
    → analyzer_agent
      ├── analysis errors → [END with error]
      └── success → question_agent
    → question_agent → answer_agent → explanation_agent → format_response → judge_agent → [END]
"""

import hashlib
import json
import logging
import time
from typing import Any, Optional

from langgraph.graph import StateGraph, END

from question_engine.state import QLCState
from question_engine.rag import rag_retrieve_node
from question_engine.agents.analyzer_agent import analyzer_agent_node
from question_engine.agents.question_agent import question_agent_node
from question_engine.agents.answer_agent import answer_agent_node
from question_engine.agents.explanation_agent import explanation_agent_node
from question_engine.agents.judge_agent import judge_agent_node

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# In-memory response cache (matches existing caching behaviour)
# ---------------------------------------------------------------------------

_response_cache: dict = {}
_CACHE_TTL_SECONDS = 3600  # 1 hour


def _cache_key(state: QLCState) -> str:
    """Derive a deterministic cache key from the parts of state that affect output."""
    config = state.get("config", {})
    payload = {
        "source_code": state.get("source_code", ""),
        "max_questions": state.get("max_questions", 10),
        "allowed_levels": sorted(config.get("include_levels", [])),
        "allowed_difficulties": sorted(config.get("include_difficulties", [])),
        "lecture_slides": state.get("lecture_slides") or "",
    }
    key_str = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(key_str.encode()).hexdigest()


def _check_cache(state: QLCState) -> Optional[dict]:
    """Return cached result if still valid, else None."""
    config = state.get("config", {})
    if not config.get("enable_caching", True):
        return None
    key = _cache_key(state)
    entry = _response_cache.get(key)
    if entry and (time.time() - entry["timestamp"]) < _CACHE_TTL_SECONDS:
        return entry["data"]
    return None


def _store_cache(state: QLCState, data: dict) -> None:
    """Store result in cache."""
    config = state.get("config", {})
    if not config.get("enable_caching", True):
        return
    key = _cache_key(state)
    _response_cache[key] = {"timestamp": time.time(), "data": data}


# ---------------------------------------------------------------------------
# Conditional routing functions
# ---------------------------------------------------------------------------

def route_rag(state: QLCState) -> str:
    """Route to RAG retrieval if lecture slides are provided."""
    if state.get("lecture_slides"):
        return "rag_retrieve"
    return "analyzer_agent"


def check_analysis_success(state: QLCState) -> str:
    """Check if analysis succeeded enough to proceed."""
    errors = state.get("analysis_errors", [])
    static = state.get("static_analysis")
    dynamic = state.get("dynamic_analysis")

    # Both completely failed → short-circuit
    static_failed = static is None or static.get("error") is not None
    dynamic_failed = dynamic is None or not dynamic.get("execution_successful", True)

    if static_failed and dynamic_failed and errors:
        logger.error("Analysis completely failed: %s", errors)
        return "error"

    # At least one succeeded → continue
    return "continue"


# ---------------------------------------------------------------------------
# Format response node (prepares final output, then triggers judge)
# ---------------------------------------------------------------------------

def format_response_node(state: QLCState) -> dict:
    """
    No-op formatting node — the questions_complete field already holds
    the final answer. This node is a hook point for any post-processing.
    """
    return {}


# ---------------------------------------------------------------------------
# Error terminal node
# ---------------------------------------------------------------------------

def error_node(state: QLCState) -> dict:
    """Terminal node for analysis failures. Ensures errors are surfaced."""
    logger.error(
        "QLC pipeline terminated early due to analysis errors: %s",
        state.get("analysis_errors", []),
    )
    return {}


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_qlc_graph():
    """
    Build and compile the QLC LangGraph StateGraph.

    Returns a compiled graph ready for graph.invoke(initial_state).
    """
    graph = StateGraph(QLCState)

    # Register nodes
    graph.add_node("rag_retrieve", rag_retrieve_node)
    graph.add_node("analyzer_agent", analyzer_agent_node)
    graph.add_node("question_agent", question_agent_node)
    graph.add_node("answer_agent", answer_agent_node)
    graph.add_node("explanation_agent", explanation_agent_node)
    graph.add_node("format_response", format_response_node)
    graph.add_node("judge_agent", judge_agent_node)
    graph.add_node("error_terminal", error_node)

    # Entry point: conditional RAG check
    graph.set_conditional_entry_point(
        route_rag,
        {
            "rag_retrieve": "rag_retrieve",
            "analyzer_agent": "analyzer_agent",
        }
    )

    # RAG → Analyzer
    graph.add_edge("rag_retrieve", "analyzer_agent")

    # Analyzer → either continue or error
    graph.add_conditional_edges(
        "analyzer_agent",
        check_analysis_success,
        {
            "continue": "question_agent",
            "error": "error_terminal",
        }
    )

    # Happy path: question → answer → explanation → format → judge → END
    graph.add_edge("question_agent", "answer_agent")
    graph.add_edge("answer_agent", "explanation_agent")
    graph.add_edge("explanation_agent", "format_response")
    graph.add_edge("format_response", "judge_agent")
    graph.add_edge("judge_agent", END)

    # Error path terminates
    graph.add_edge("error_terminal", END)

    return graph.compile()


# Singleton graph instance (built once at import time, re-used across requests)
_qlc_graph = None


def get_qlc_graph():
    """Return the singleton compiled graph, building it on first call."""
    global _qlc_graph
    if _qlc_graph is None:
        logger.info("Building QLC LangGraph pipeline...")
        _qlc_graph = build_qlc_graph()
        logger.info("QLC LangGraph pipeline ready.")
    return _qlc_graph


def run_pipeline(
    source_code: str,
    max_questions: int = 10,
    lecture_slides: Optional[str] = None,
    config: Optional[dict] = None,
) -> QLCState:
    """
    Convenience function: run the full QLC pipeline and return final state.

    Checks the cache first. On miss, invokes the graph and caches the result.

    Args:
        source_code: Student's Python code.
        max_questions: Maximum number of questions to generate.
        lecture_slides: Optional raw text of lecture slides for RAG.
        config: Optional config dict (keys match GenerationConfig fields).

    Returns:
        Final QLCState dict after graph execution.
    """
    from question_engine.state import make_initial_state

    cfg = config or {}
    initial_state = make_initial_state(
        source_code=source_code,
        max_questions=max_questions,
        lecture_slides=lecture_slides,
        config=cfg,
    )

    # Cache check
    cached = _check_cache(initial_state)
    if cached:
        logger.info("QLC pipeline: cache hit")
        cached["from_cache"] = True
        return cached

    graph = get_qlc_graph()
    logger.info("QLC pipeline: invoking graph (max_questions=%d)", max_questions)
    result = graph.invoke(initial_state)

    # Store successful results
    if result.get("questions_complete"):
        _store_cache(initial_state, dict(result))

    return result
