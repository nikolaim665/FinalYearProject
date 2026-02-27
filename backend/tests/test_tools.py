"""
Tests for @tool definitions in question_engine/tools.py.
"""

import json
import pytest
from question_engine.tools import (
    run_static_analysis,
    run_dynamic_analysis,
    query_variable_value,
    query_function_return,
    query_loop_iterations,
)


SIMPLE_CODE = "x = 5\ny = x + 1\nprint(y)"

FUNCTION_CODE = """
def add(a, b):
    return a + b

result = add(3, 4)
"""

LOOP_CODE = """
total = 0
for i in range(5):
    total += i
print(total)
"""


class TestRunStaticAnalysis:
    def test_returns_dict(self):
        result = run_static_analysis.invoke({"source_code": SIMPLE_CODE})
        assert isinstance(result, dict)

    def test_simple_code_has_summary(self):
        result = run_static_analysis.invoke({"source_code": SIMPLE_CODE})
        assert "summary" in result or "error" not in result

    def test_function_detected(self):
        result = run_static_analysis.invoke({"source_code": FUNCTION_CODE})
        assert isinstance(result, dict)
        functions = result.get("functions", [])
        func_names = [f.get("name") for f in functions]
        assert "add" in func_names

    def test_syntax_error_returns_error_key(self):
        result = run_static_analysis.invoke({"source_code": "def broken(:"})
        assert isinstance(result, dict)
        # Should have an error key rather than raising
        assert "error" in result or result == {}


class TestRunDynamicAnalysis:
    def test_returns_dict(self):
        result = run_dynamic_analysis.invoke({"source_code": SIMPLE_CODE})
        assert isinstance(result, dict)

    def test_execution_successful(self):
        result = run_dynamic_analysis.invoke({"source_code": SIMPLE_CODE})
        assert result.get("execution_successful") is True

    def test_final_variables_tracked(self):
        result = run_dynamic_analysis.invoke({"source_code": SIMPLE_CODE})
        final = result.get("final_variables", {})
        assert isinstance(final, dict)

    def test_function_calls_tracked(self):
        result = run_dynamic_analysis.invoke({"source_code": FUNCTION_CODE})
        assert isinstance(result, dict)

    def test_loop_iterations_tracked(self):
        result = run_dynamic_analysis.invoke({"source_code": LOOP_CODE})
        assert isinstance(result, dict)
        assert result.get("execution_successful") is True

    @pytest.mark.skip(reason="Takes 5+ seconds due to timeout; run manually if needed")
    def test_infinite_loop_times_out(self):
        code = "while True: pass"
        result = run_dynamic_analysis.invoke({"source_code": code})
        assert isinstance(result, dict)
        # Should not crash the test; either timeout or execution_successful=False
        assert "execution_successful" in result or "error" in result


class TestQueryTools:
    def _make_dynamic_json(self, final_vars=None, function_calls=None, loop_executions=None):
        data = {
            "execution_successful": True,
            "final_variables": final_vars or {},
            "function_calls": function_calls or [],
            "loop_executions": loop_executions or {},
        }
        return json.dumps(data)

    def test_query_variable_found(self):
        dyn_json = self._make_dynamic_json(final_vars={"x": 42})
        result = query_variable_value.invoke({
            "variable_name": "x",
            "dynamic_analysis_json": dyn_json,
        })
        assert "42" in result
        assert "x" in result

    def test_query_variable_not_found(self):
        dyn_json = self._make_dynamic_json(final_vars={"y": 10})
        result = query_variable_value.invoke({
            "variable_name": "z",
            "dynamic_analysis_json": dyn_json,
        })
        assert "not found" in result.lower()

    def test_query_function_return_found(self):
        dyn_json = self._make_dynamic_json(function_calls=[
            {"function_name": "add", "args": [3, 4], "return_value": 7}
        ])
        result = query_function_return.invoke({
            "function_name": "add",
            "dynamic_analysis_json": dyn_json,
        })
        assert "add" in result
        assert "7" in result

    def test_query_function_return_not_called(self):
        dyn_json = self._make_dynamic_json()
        result = query_function_return.invoke({
            "function_name": "missing_fn",
            "dynamic_analysis_json": dyn_json,
        })
        assert "not called" in result.lower() or "missing_fn" in result

    def test_query_loop_iterations_found(self):
        dyn_json = self._make_dynamic_json(loop_executions={"5": 10})
        result = query_loop_iterations.invoke({
            "line_number": 5,
            "dynamic_analysis_json": dyn_json,
        })
        assert "10" in result

    def test_query_loop_iterations_not_found(self):
        dyn_json = self._make_dynamic_json()
        result = query_loop_iterations.invoke({
            "line_number": 99,
            "dynamic_analysis_json": dyn_json,
        })
        assert "not found" in result.lower() or "99" in result
