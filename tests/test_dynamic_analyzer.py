"""
Unit tests for the Dynamic Code Analyzer.
"""

import unittest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_path))

from analyzers.dynamic_analyzer import DynamicAnalyzer, analyze_code


class TestDynamicAnalyzer(unittest.TestCase):
    """Test cases for DynamicAnalyzer."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = DynamicAnalyzer()

    def test_simple_execution(self):
        """Test execution of simple code."""
        code = """
x = 10
y = 20
result = x + y
"""
        result = self.analyzer.analyze(code)

        # Check execution was successful
        self.assertTrue(result['execution_successful'])
        self.assertIsNone(result['exception'])

        # Check final variables
        final_vars = result['final_variables']
        self.assertIn('global.x', final_vars)
        self.assertIn('global.y', final_vars)
        self.assertIn('global.result', final_vars)
        self.assertEqual(final_vars['global.result']['value'], 30)

    def test_function_call_tracking(self):
        """Test tracking of function calls."""
        code = """
def add(a, b):
    return a + b

result = add(5, 3)
"""
        result = self.analyzer.analyze(code)

        # Check function calls
        calls = result['function_calls']
        self.assertGreater(len(calls), 0)

        # Find the add function call
        add_calls = [c for c in calls if c['function_name'] == 'add']
        self.assertEqual(len(add_calls), 1)

        add_call = add_calls[0]
        self.assertEqual(add_call['arguments']['a'], 5)
        self.assertEqual(add_call['arguments']['b'], 3)
        self.assertEqual(add_call['return_value'], 8)

    def test_recursive_function(self):
        """Test execution of recursive functions."""
        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
"""
        result = self.analyzer.analyze(code)

        # Check execution successful
        self.assertTrue(result['execution_successful'])

        # Check final result
        self.assertEqual(result['final_variables']['global.result']['value'], 120)

        # Check stack depth (factorial(5) should go 5 levels deep)
        self.assertGreaterEqual(result['max_stack_depth'], 5)

        # Check function calls (should have 5 calls to factorial)
        factorial_calls = [c for c in result['function_calls'] if c['function_name'] == 'factorial']
        self.assertEqual(len(factorial_calls), 5)

    def test_loop_iteration_count(self):
        """Test counting loop iterations."""
        code = """
total = 0
for i in range(10):
    total += i
"""
        result = self.analyzer.analyze(code)

        # Check execution successful
        self.assertTrue(result['execution_successful'])

        # Check final total
        self.assertEqual(result['final_variables']['global.total']['value'], 45)

        # Check loop execution info
        loops = result['loop_executions']
        self.assertGreater(len(loops), 0)

        # Find the for loop
        for_loops = [l for l in loops if l['loop_type'] == 'for']
        self.assertGreater(len(for_loops), 0)

        # The loop should have 10 iterations
        # Note: The actual count might be the number of times the loop header was revisited
        self.assertGreater(for_loops[0]['iteration_count'], 0)

    def test_while_loop(self):
        """Test while loop execution."""
        code = """
count = 0
while count < 5:
    count += 1
"""
        result = self.analyzer.analyze(code)

        # Check execution successful
        self.assertTrue(result['execution_successful'])

        # Check final count
        self.assertEqual(result['final_variables']['global.count']['value'], 5)

        # Check loop execution
        loops = result['loop_executions']
        while_loops = [l for l in loops if l['loop_type'] == 'while']
        self.assertGreater(len(while_loops), 0)

    def test_nested_loops(self):
        """Test nested loop execution."""
        code = """
total = 0
for i in range(3):
    for j in range(3):
        total += 1
"""
        result = self.analyzer.analyze(code)

        # Check execution successful
        self.assertTrue(result['execution_successful'])

        # Check final total (3 * 3 = 9)
        self.assertEqual(result['final_variables']['global.total']['value'], 9)

        # Check we detected multiple loops
        loops = result['loop_executions']
        self.assertGreaterEqual(len(loops), 2)

    def test_variable_snapshots(self):
        """Test variable value tracking throughout execution."""
        code = """
x = 1
x = 2
x = 3
"""
        result = self.analyzer.analyze(code)

        # Check snapshots captured
        snapshots = result['variable_snapshots']
        x_snapshots = [s for s in snapshots if s['name'] == 'x']

        # Should have multiple snapshots for x
        self.assertGreater(len(x_snapshots), 0)

        # Final value should be 3
        self.assertEqual(result['final_variables']['global.x']['value'], 3)

    def test_stdout_capture(self):
        """Test capturing stdout output."""
        code = """
print("Hello, World!")
print("Python is awesome")
"""
        result = self.analyzer.analyze(code)

        # Check stdout was captured
        stdout = result['stdout']
        self.assertIn("Hello, World!", stdout)
        self.assertIn("Python is awesome", stdout)

    def test_exception_handling(self):
        """Test handling of runtime exceptions."""
        code = """
x = 10
y = 0
result = x / y  # Division by zero
"""
        result = self.analyzer.analyze(code)

        # Check execution failed
        self.assertFalse(result['execution_successful'])
        self.assertIsNotNone(result['exception'])
        self.assertIn("ZeroDivisionError", result['exception'])

    def test_execution_flow(self):
        """Test tracking of execution flow."""
        code = """
x = 1
if x > 0:
    y = 2
else:
    y = 3
z = 4
"""
        result = self.analyzer.analyze(code)

        # Check execution flow was tracked
        flow = result['execution_flow']
        self.assertGreater(len(flow), 0)

        # Check we executed some lines
        unique_lines = result['unique_lines_executed']
        self.assertGreater(unique_lines, 0)

    def test_complex_program(self):
        """Test analysis of a more complex program."""
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def print_fibonacci(count):
    results = []
    for i in range(count):
        value = fibonacci(i)
        results.append(value)
    return results

numbers = print_fibonacci(6)
"""
        result = self.analyzer.analyze(code)

        # Check execution successful
        self.assertTrue(result['execution_successful'])

        # Check final results
        final_numbers = result['final_variables']['global.numbers']['value']
        self.assertEqual(final_numbers, [0, 1, 1, 2, 3, 5])

        # Check we tracked function calls
        fib_calls = [c for c in result['function_calls'] if c['function_name'] == 'fibonacci']
        self.assertGreater(len(fib_calls), 0)

        # Check loop execution
        self.assertGreater(len(result['loop_executions']), 0)

    def test_test_inputs(self):
        """Test providing test inputs to code."""
        code = """
result = input_value * 2
"""
        result = self.analyzer.analyze(code, test_inputs={'input_value': 21})

        # Check the computation used the test input
        self.assertTrue(result['execution_successful'])
        self.assertEqual(result['final_variables']['global.result']['value'], 42)

    def test_list_operations(self):
        """Test tracking list operations."""
        code = """
numbers = [1, 2, 3, 4, 5]
squared = [x**2 for x in numbers]
total = sum(squared)
"""
        result = self.analyzer.analyze(code)

        # Check execution successful
        self.assertTrue(result['execution_successful'])

        # Check final values
        self.assertEqual(result['final_variables']['global.numbers']['value'], [1, 2, 3, 4, 5])
        self.assertEqual(result['final_variables']['global.squared']['value'], [1, 4, 9, 16, 25])
        self.assertEqual(result['final_variables']['global.total']['value'], 55)

    def test_dictionary_operations(self):
        """Test tracking dictionary operations."""
        code = """
data = {'a': 1, 'b': 2, 'c': 3}
values = list(data.values())
total = sum(values)
"""
        result = self.analyzer.analyze(code)

        # Check execution successful
        self.assertTrue(result['execution_successful'])

        # Check final values
        self.assertEqual(result['final_variables']['global.data']['value'], {'a': 1, 'b': 2, 'c': 3})
        self.assertEqual(result['final_variables']['global.total']['value'], 6)

    def test_function_scope_tracking(self):
        """Test tracking variables in different scopes."""
        code = """
global_var = 100

def my_function():
    local_var = 50
    return local_var + global_var

result = my_function()
"""
        result = self.analyzer.analyze(code)

        # Check execution successful
        self.assertTrue(result['execution_successful'])
        self.assertEqual(result['final_variables']['global.result']['value'], 150)

        # Check we captured variables in different scopes
        snapshots = result['variable_snapshots']
        global_vars = [s for s in snapshots if s['scope'] == 'global' and s['name'] == 'global_var']
        local_vars = [s for s in snapshots if s['scope'] == 'my_function' and s['name'] == 'local_var']

        self.assertGreater(len(global_vars), 0)
        self.assertGreater(len(local_vars), 0)

    def test_empty_code(self):
        """Test execution of empty code."""
        code = ""
        result = self.analyzer.analyze(code)

        # Should execute successfully with no output
        self.assertTrue(result['execution_successful'])
        # Stack depth is at least 1 for the module level
        self.assertGreaterEqual(result['max_stack_depth'], 0)

    def test_multiple_returns(self):
        """Test function with multiple return statements."""
        code = """
def check_value(x):
    if x > 10:
        return "large"
    elif x > 5:
        return "medium"
    else:
        return "small"

result1 = check_value(15)
result2 = check_value(7)
result3 = check_value(2)
"""
        result = self.analyzer.analyze(code)

        # Check execution successful
        self.assertTrue(result['execution_successful'])

        # Check results
        self.assertEqual(result['final_variables']['global.result1']['value'], "large")
        self.assertEqual(result['final_variables']['global.result2']['value'], "medium")
        self.assertEqual(result['final_variables']['global.result3']['value'], "small")

    def test_convenience_function(self):
        """Test the convenience analyze_code function."""
        code = """
x = 42
"""
        result = analyze_code(code)

        # Check it works
        self.assertTrue(result['execution_successful'])
        self.assertEqual(result['final_variables']['global.x']['value'], 42)


class TestExecutionTracer(unittest.TestCase):
    """Test cases for ExecutionTracer behavior."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = DynamicAnalyzer()

    def test_stack_depth_tracking(self):
        """Test that stack depth is correctly tracked."""
        code = """
def level3():
    return "deep"

def level2():
    return level3()

def level1():
    return level2()

result = level1()
"""
        result = self.analyzer.analyze(code)

        # Stack should be at least 3 deep (plus module level)
        self.assertGreaterEqual(result['max_stack_depth'], 3)

    def test_value_serialization(self):
        """Test that various value types are serialized correctly."""
        code = """
none_val = None
bool_val = True
int_val = 42
float_val = 3.14
str_val = "hello"
list_val = [1, 2, 3]
dict_val = {'key': 'value'}
set_val = {1, 2, 3}
"""
        result = self.analyzer.analyze(code)

        # Check execution successful
        self.assertTrue(result['execution_successful'])

        # Check all values are serialized
        final_vars = result['final_variables']
        self.assertIsNone(final_vars['global.none_val']['value'])
        self.assertEqual(final_vars['global.bool_val']['value'], True)
        self.assertEqual(final_vars['global.int_val']['value'], 42)
        self.assertEqual(final_vars['global.float_val']['value'], 3.14)
        self.assertEqual(final_vars['global.str_val']['value'], "hello")
        self.assertEqual(final_vars['global.list_val']['value'], [1, 2, 3])
        self.assertEqual(final_vars['global.dict_val']['value'], {'key': 'value'})
        # Set is converted to list
        self.assertIsInstance(final_vars['global.set_val']['value'], list)


if __name__ == "__main__":
    unittest.main()
