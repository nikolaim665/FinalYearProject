"""
Unit tests for the Static Code Analyzer.
"""

import unittest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_path))

from analyzers.static_analyzer import StaticAnalyzer, analyze_code


class TestStaticAnalyzer(unittest.TestCase):
    """Test cases for StaticAnalyzer."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = StaticAnalyzer()

    def test_simple_function(self):
        """Test analysis of a simple function."""
        code = """
def greet(name):
    return f"Hello, {name}"
"""
        result = self.analyzer.analyze(code)

        # Check functions
        self.assertEqual(len(result["functions"]), 1)
        func = result["functions"][0]
        self.assertEqual(func["name"], "greet")
        self.assertEqual(func["params"], ["name"])
        self.assertEqual(func["param_count"], 1)
        self.assertFalse(func["is_recursive"])

    def test_recursive_function(self):
        """Test detection of recursive functions."""
        code = """
def factorial(n):
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)
"""
        result = self.analyzer.analyze(code)

        # Check recursion detection
        self.assertEqual(len(result["functions"]), 1)
        func = result["functions"][0]
        self.assertEqual(func["name"], "factorial")
        self.assertTrue(func["is_recursive"])
        self.assertTrue(func["has_conditionals"])
        self.assertEqual(func["return_count"], 2)

    def test_variables(self):
        """Test variable detection."""
        code = """
x = 10
y = 20

def calculate():
    result = x + y
    return result

z = calculate()
"""
        result = self.analyzer.analyze(code)

        # Check variables
        variables = result["variables"]
        var_names = [v["name"] for v in variables]
        self.assertIn("x", var_names)
        self.assertIn("y", var_names)
        self.assertIn("z", var_names)
        self.assertIn("result", var_names)

        # Check scopes
        x_var = next(v for v in variables if v["name"] == "x")
        self.assertEqual(x_var["scope"], "global")

        result_var = next(v for v in variables if v["name"] == "result")
        self.assertEqual(result_var["scope"], "calculate")

    def test_loops(self):
        """Test loop detection."""
        code = """
for i in range(10):
    print(i)

j = 0
while j < 5:
    j += 1
"""
        result = self.analyzer.analyze(code)

        # Check loops
        self.assertEqual(len(result["loops"]), 2)

        # Check for loop
        for_loop = result["loops"][0]
        self.assertEqual(for_loop["type"], "for")
        self.assertEqual(for_loop["loop_variable"], "i")
        self.assertEqual(for_loop["nesting_level"], 0)

        # Check while loop
        while_loop = result["loops"][1]
        self.assertEqual(while_loop["type"], "while")
        self.assertEqual(while_loop["nesting_level"], 0)

    def test_nested_loops(self):
        """Test nested loop detection."""
        code = """
for i in range(3):
    for j in range(3):
        print(i, j)
"""
        result = self.analyzer.analyze(code)

        # Check nested loops
        self.assertEqual(len(result["loops"]), 2)
        outer_loop = result["loops"][0]
        inner_loop = result["loops"][1]

        self.assertEqual(outer_loop["nesting_level"], 0)
        self.assertEqual(inner_loop["nesting_level"], 1)

    def test_conditionals(self):
        """Test conditional detection."""
        code = """
x = 10

if x > 5:
    print("greater")
elif x == 5:
    print("equal")
else:
    print("less")

if x < 20:
    print("yes")
"""
        result = self.analyzer.analyze(code)

        # Check conditionals (elif creates a nested If node, so we get 3 total)
        # 1st: main if with elif/else
        # 2nd: the elif (which is an If in the else block)
        # 3rd: the second independent if
        self.assertGreaterEqual(len(result["conditionals"]), 2)

        first_if = result["conditionals"][0]
        self.assertTrue(first_if["has_elif"] or first_if["has_else"])

        # Find the standalone if statement (the one on line checking x < 20)
        standalone_ifs = [
            c for c in result["conditionals"] if not c["has_elif"] and not c["has_else"]
        ]
        self.assertGreaterEqual(len(standalone_ifs), 1)

    def test_function_calls(self):
        """Test function call detection."""
        code = """
def helper(x):
    return x * 2

def main():
    result = helper(5)
    print(result)
    return result

output = main()
"""
        result = self.analyzer.analyze(code)

        # Check function calls
        calls = result["function_calls"]
        call_names = [c["function"] for c in calls]

        self.assertIn("helper", call_names)
        self.assertIn("print", call_names)
        self.assertIn("main", call_names)

        # Check helper call details
        helper_call = next(c for c in calls if c["function"] == "helper")
        self.assertEqual(helper_call["arguments_count"], 1)

    def test_complex_program(self):
        """Test analysis of a more complex program."""
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def print_fibonacci(count):
    for i in range(count):
        value = fibonacci(i)
        print(f"F({i}) = {value}")

numbers = 10
print_fibonacci(numbers)
"""
        result = self.analyzer.analyze(code)

        # Check summary
        summary = result["summary"]
        self.assertEqual(summary["total_functions"], 2)
        self.assertTrue(summary["has_recursion"])
        self.assertGreater(summary["total_loops"], 0)

        # Check fibonacci function
        fib_func = next(f for f in result["functions"] if f["name"] == "fibonacci")
        self.assertTrue(fib_func["is_recursive"])
        self.assertTrue(fib_func["has_conditionals"])

        # Check print_fibonacci function
        print_func = next(
            f for f in result["functions"] if f["name"] == "print_fibonacci"
        )
        self.assertTrue(print_func["has_loops"])

    def test_syntax_error(self):
        """Test handling of syntax errors."""
        code = """
def broken(:
    return 42
"""
        with self.assertRaises(SyntaxError):
            self.analyzer.analyze(code)

    def test_empty_code(self):
        """Test analysis of empty code."""
        code = ""
        result = self.analyzer.analyze(code)

        self.assertEqual(len(result["functions"]), 0)
        self.assertEqual(len(result["variables"]), 0)
        self.assertEqual(result["summary"]["total_functions"], 0)

    def test_line_numbers(self):
        """Test that line numbers are correctly tracked."""
        code = """
def example():
    x = 1
    y = 2
    return x + y
"""
        result = self.analyzer.analyze(code)

        func = result["functions"][0]
        self.assertEqual(func["line_start"], 2)
        self.assertGreaterEqual(func["line_end"], func["line_start"])

    def test_multiple_functions(self):
        """Test analysis of multiple functions."""
        code = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b
"""
        result = self.analyzer.analyze(code)

        self.assertEqual(len(result["functions"]), 3)
        func_names = [f["name"] for f in result["functions"]]
        self.assertIn("add", func_names)
        self.assertIn("subtract", func_names)
        self.assertIn("multiply", func_names)

    def test_convenience_function(self):
        """Test the convenience analyze_code function."""
        code = """
def test():
    return 42
"""
        result = analyze_code(code)

        self.assertIn("functions", result)
        self.assertEqual(len(result["functions"]), 1)


class TestCodeVisitor(unittest.TestCase):
    """Test cases for CodeVisitor behavior."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = StaticAnalyzer()

    def test_function_calls_tracking(self):
        """Test that function calls are properly tracked."""
        code = """
def helper():
    return 1

def main():
    x = helper()
    y = helper()
    return x + y
"""
        result = self.analyzer.analyze(code)

        main_func = next(f for f in result["functions"] if f["name"] == "main")
        self.assertIn("helper", main_func["calls_functions"])

    def test_builtin_calls(self):
        """Test detection of builtin function calls."""
        code = """
def process(items):
    result = list(items)
    print(len(result))
    return result
"""
        result = self.analyzer.analyze(code)

        calls = result["function_calls"]
        call_names = [c["function"] for c in calls]
        self.assertIn("list", call_names)
        self.assertIn("print", call_names)
        self.assertIn("len", call_names)


if __name__ == "__main__":
    unittest.main()
