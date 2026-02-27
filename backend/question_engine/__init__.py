"""
Question Engine Package

LangGraph-powered multi-agent question generation system.
Analyzes student code (static + dynamic) and generates
pedagogically valuable comprehension questions via a pipeline of
specialised agents.
"""

# Primary entry point: run the full LangGraph pipeline
from question_engine.graph import run_pipeline, get_qlc_graph, build_qlc_graph

# State type
from question_engine.state import QLCState, make_initial_state

__all__ = [
    # Pipeline
    "run_pipeline",
    "get_qlc_graph",
    "build_qlc_graph",
    # State
    "QLCState",
    "make_initial_state",
]
