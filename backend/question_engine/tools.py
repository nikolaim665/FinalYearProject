"""
LangChain Tool Definitions for the QLC Pipeline

All @tool-decorated functions that agents can call to interact with
the static/dynamic analysers or query analysis results.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

# Ensure backend package is importable
_backend_path = Path(__file__).parent.parent
if str(_backend_path) not in sys.path:
    sys.path.insert(0, str(_backend_path))

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Primary analysis tools (used by Analyzer Agent)
# ---------------------------------------------------------------------------

@tool
def run_static_analysis(source_code: str) -> dict:
    """Analyse Python source code structure using AST parsing.

    Returns structural information including: functions (with params, recursion,
    complexity), classes (with methods, inheritance), variables (with scope, type
    annotations), loops (with type, nesting), conditionals, comprehensions,
    exception handlers, imports, and context managers.

    Args:
        source_code: Raw Python source code string.

    Returns:
        dict with keys: functions, classes, variables, loops, conditionals,
        imports, comprehensions, exception_handlers, context_managers, summary.
    """
    from analyzers.static_analyzer import StaticAnalyzer
    analyzer = StaticAnalyzer()
    try:
        result = analyzer.analyze(source_code)
        return result if isinstance(result, dict) else {}
    except Exception as e:
        logger.error("Static analysis failed: %s", e)
        return {"error": str(e), "execution_successful": False}


@tool
def run_dynamic_analysis(source_code: str) -> dict:
    """Execute Python code and trace runtime behaviour.

    Returns: variable values at each line, final variable values, function call
    arguments and return values, loop iteration counts, recursion depth, stdout
    output, and execution success/failure status.

    Code execution is sandboxed with a 5-second timeout.

    Args:
        source_code: Raw Python source code string (may include a test driver).

    Returns:
        dict with keys: execution_successful, final_variables, function_calls,
        loop_executions, max_stack_depth, stdout, error_message.
    """
    from analyzers.dynamic_analyzer import DynamicAnalyzer
    analyzer = DynamicAnalyzer(timeout=5)
    try:
        result = analyzer.analyze(source_code)
        return result if isinstance(result, dict) else {}
    except Exception as e:
        logger.error("Dynamic analysis failed: %s", e)
        return {"error": str(e), "execution_successful": False}


# ---------------------------------------------------------------------------
# Query tools (used by Answer Agent to verify answers)
# ---------------------------------------------------------------------------

# These are stateful helpers — they receive analysis data as arguments rather
# than reading from a shared store, keeping tools pure and testable.

@tool
def query_variable_value(variable_name: str, dynamic_analysis_json: str) -> str:
    """Look up the final runtime value of a specific variable from dynamic analysis.

    Args:
        variable_name: Name of the variable to look up.
        dynamic_analysis_json: JSON-encoded dynamic analysis dict from run_dynamic_analysis().

    Returns:
        String describing the variable's final value and type,
        or 'not found' if the variable doesn't exist in the trace.
    """
    try:
        analysis = json.loads(dynamic_analysis_json)
        final_vars = analysis.get("final_variables", {})
        if variable_name in final_vars:
            value = final_vars[variable_name]
            return f"{variable_name} = {value!r} (type: {type(value).__name__})"
        # Also check variable_trace
        trace = analysis.get("variable_trace", {})
        if variable_name in trace:
            values = trace[variable_name]
            last = values[-1] if values else None
            return f"{variable_name} last seen as {last!r}"
        return f"Variable '{variable_name}' not found in dynamic analysis trace."
    except Exception as e:
        return f"Error querying variable value: {e}"


@tool
def query_function_return(function_name: str, dynamic_analysis_json: str) -> str:
    """Look up what a specific function returns when called during execution.

    Args:
        function_name: Name of the function to look up.
        dynamic_analysis_json: JSON-encoded dynamic analysis dict.

    Returns:
        String describing the return value(s) from the function's calls.
    """
    try:
        analysis = json.loads(dynamic_analysis_json)
        calls = analysis.get("function_calls", [])
        relevant = [c for c in calls if c.get("function_name") == function_name]
        if not relevant:
            return f"Function '{function_name}' was not called during execution."
        lines = []
        for c in relevant:
            ret = c.get("return_value", "<no return>")
            args = c.get("args", [])
            lines.append(f"{function_name}({args}) -> {ret!r}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error querying function return: {e}"


@tool
def query_loop_iterations(line_number: int, dynamic_analysis_json: str) -> str:
    """Look up how many times a loop at a specific line executed.

    Args:
        line_number: Line number of the loop statement.
        dynamic_analysis_json: JSON-encoded dynamic analysis dict.

    Returns:
        String with the iteration count, or a not-found message.
    """
    try:
        analysis = json.loads(dynamic_analysis_json)
        loops = analysis.get("loop_executions", {})
        key = str(line_number)
        if key in loops:
            return f"Loop at line {line_number} executed {loops[key]} time(s)."
        # Try integer key
        if line_number in loops:
            return f"Loop at line {line_number} executed {loops[line_number]} time(s)."
        # Fallback: look through loop_iterations list if present
        loop_list = analysis.get("loop_iterations", [])
        for entry in loop_list:
            if entry.get("line") == line_number:
                return f"Loop at line {line_number} executed {entry.get('count', '?')} time(s)."
        return f"No loop iteration data found for line {line_number}."
    except Exception as e:
        return f"Error querying loop iterations: {e}"
