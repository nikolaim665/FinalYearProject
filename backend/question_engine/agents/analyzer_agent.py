"""
Analyzer Agent Node

Runs static and dynamic analysis on student code.
Optionally generates a test driver if the code has no top-level function calls.
"""

import json
import logging
import os
import re
import time
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from question_engine.state import QLCState
from question_engine.tools import run_static_analysis, run_dynamic_analysis

logger = logging.getLogger(__name__)

ANALYZER_SYSTEM_PROMPT = """You are a code analysis orchestrator. Your job is to analyse student Python code
by calling the static and dynamic analysis tools. Always run static analysis first.
If the code defines functions but has no top-level calls, generate a test driver first,
then run dynamic analysis with the augmented code.

Report all results faithfully. Do not interpret or summarise — just run the tools
and return their output."""

DRIVER_SYSTEM_PROMPT = """You are a Python test driver generator. Given Python code that defines functions
but does not call them at module level, generate a minimal try/except-wrapped snippet
that calls each function with representative inputs.

Rules:
- Use variable names prefixed with _qlc_r (e.g. _qlc_r1, _qlc_r2) to store results
- Wrap each call in try/except Exception: pass to prevent crashes
- Generate 1-3 calls total; prefer the most interesting inputs
- Output ONLY the driver code, no explanation, no markdown fences

Example output for def factorial(n):
try:
    _qlc_r1 = factorial(5)
except Exception:
    pass
"""


def _has_top_level_calls(static_analysis: dict) -> bool:
    """Return True if the code has any module-level function calls."""
    # Check the summary flag if present
    summary = static_analysis.get("summary", {})
    if summary.get("has_module_level_calls") is not None:
        return bool(summary["has_module_level_calls"])

    # Fallback: check if dynamic analysis would have something to trace
    # by looking at whether there are any top-level statements that are calls
    functions = static_analysis.get("functions", [])
    if not functions:
        return True  # No functions → nothing to drive

    # If static analysis returned call_count or similar hints, use them
    for fn in functions:
        if fn.get("call_count", 0) > 0:
            return True

    return False


def _generate_test_driver(source_code: str, static_analysis: dict, model: str) -> str:
    """Use a cheap LLM call to generate a test driver snippet."""
    function_names = [
        fn.get("name", "") for fn in static_analysis.get("functions", [])
        if fn.get("name")
    ]
    if not function_names:
        return ""

    llm = ChatOpenAI(model=model, temperature=0.2)
    user_msg = (
        f"Generate a test driver for the following Python functions: "
        f"{', '.join(function_names)}\n\nSource code:\n```python\n{source_code}\n```"
    )
    response = llm.invoke([
        SystemMessage(content=DRIVER_SYSTEM_PROMPT),
        HumanMessage(content=user_msg),
    ])
    driver_code = response.content.strip()
    # Strip any accidental markdown fences
    driver_code = re.sub(r"^```python\n?", "", driver_code)
    driver_code = re.sub(r"```$", "", driver_code).strip()
    return driver_code


def analyzer_agent_node(state: QLCState) -> dict:
    """
    LangGraph node: Run static and dynamic analysis.

    Updates state with:
    - static_analysis
    - dynamic_analysis
    - analysis_warnings
    - analysis_errors
    - execution_time_ms (partial)
    """
    start = time.time()
    source_code: str = state["source_code"]
    config: dict = state.get("config", {})
    driver_model: str = config.get("driver_model", "gpt-4o-mini")
    enable_auto_driver: bool = config.get("enable_auto_driver", True)

    warnings: list[str] = list(state.get("analysis_warnings", []))
    errors: list[str] = list(state.get("analysis_errors", []))

    # --- Static Analysis ---
    static_result: dict = {}
    try:
        logger.info("Analyzer agent: running static analysis")
        static_result = run_static_analysis.invoke({"source_code": source_code})
        if static_result.get("error"):
            errors.append(f"Static analysis error: {static_result['error']}")
    except Exception as e:
        logger.error("Static analysis raised exception: %s", e)
        errors.append(f"Static analysis exception: {e}")

    # --- Optional test driver generation ---
    augmented_code = source_code
    if enable_auto_driver and static_result and not static_result.get("error"):
        if not _has_top_level_calls(static_result):
            logger.info("Analyzer agent: no top-level calls detected — generating test driver")
            try:
                driver = _generate_test_driver(source_code, static_result, driver_model)
                if driver:
                    augmented_code = source_code + "\n\n# --- QLC Test Driver ---\n" + driver
                    warnings.append("Auto-generated test driver appended for dynamic analysis.")
                    logger.info("Test driver generated and appended.")
            except Exception as e:
                logger.warning("Test driver generation failed: %s", e)
                warnings.append(f"Test driver generation failed: {e}")

    # --- Dynamic Analysis ---
    dynamic_result: dict = {}
    try:
        logger.info("Analyzer agent: running dynamic analysis")
        dynamic_result = run_dynamic_analysis.invoke({"source_code": augmented_code})
        if dynamic_result.get("error") and not dynamic_result.get("execution_successful"):
            warnings.append(f"Dynamic analysis warning: {dynamic_result.get('error', 'unknown')}")
    except Exception as e:
        logger.error("Dynamic analysis raised exception: %s", e)
        warnings.append(f"Dynamic analysis exception: {e}")
        dynamic_result = {"execution_successful": False, "error": str(e)}

    # --- Fatal error check ---
    if static_result.get("error") and not dynamic_result.get("execution_successful"):
        errors.append("Both static and dynamic analysis failed.")

    elapsed = (time.time() - start) * 1000

    return {
        "static_analysis": static_result or None,
        "dynamic_analysis": dynamic_result or None,
        "analysis_warnings": warnings,
        "analysis_errors": errors,
        "execution_time_ms": state.get("execution_time_ms", 0.0) + elapsed,
    }
