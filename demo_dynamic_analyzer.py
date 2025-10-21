"""
Demo script for the Dynamic Code Analyzer.

Demonstrates the capabilities of the dynamic analyzer by executing
sample Python programs and showing the runtime information collected.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_path))

from analyzers.dynamic_analyzer import DynamicAnalyzer
import json


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(label: str, value):
    """Print a labeled result."""
    print(f"{label:30} {value}")


def demo_simple_execution():
    """Demo: Simple variable assignments and arithmetic."""
    print_section("Demo 1: Simple Execution")

    code = """
x = 10
y = 20
result = x + y
print(f"The result is {result}")
"""

    print("Code:")
    print(code)

    analyzer = DynamicAnalyzer()
    result = analyzer.analyze(code)

    print("\nResults:")
    print_result("Execution Successful:", result['execution_successful'])
    print_result("Lines Executed:", result['total_lines_executed'])
    print_result("Unique Lines:", result['unique_lines_executed'])
    print_result("Max Stack Depth:", result['max_stack_depth'])

    print("\nFinal Variables:")
    for var_name, var_info in result['final_variables'].items():
        print(f"  {var_name}: {var_info['value']} (type: {var_info['type']})")

    print("\nOutput:")
    print(result['stdout'])


def demo_function_calls():
    """Demo: Function call tracking with return values."""
    print_section("Demo 2: Function Call Tracking")

    code = """
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

result1 = add(5, 3)
result2 = multiply(4, 7)
final = add(result1, result2)
"""

    print("Code:")
    print(code)

    analyzer = DynamicAnalyzer()
    result = analyzer.analyze(code)

    print("\nFunction Calls:")
    for call in result['function_calls']:
        args_str = ", ".join(f"{k}={v}" for k, v in call['arguments'].items())
        print(f"  {call['function_name']}({args_str}) -> {call['return_value']}")
        print(f"    Line: {call['line']}, Stack Depth: {call['stack_depth']}")

    print("\nFinal Variables:")
    for var_name, var_info in result['final_variables'].items():
        if not var_name.startswith('global.result') and not var_name.startswith('global.final'):
            continue
        print(f"  {var_name}: {var_info['value']}")


def demo_recursion():
    """Demo: Recursive function with stack depth tracking."""
    print_section("Demo 3: Recursive Function (Factorial)")

    code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
print(f"5! = {result}")
"""

    print("Code:")
    print(code)

    analyzer = DynamicAnalyzer()
    result = analyzer.analyze(code)

    print("\nResults:")
    print_result("Max Stack Depth:", result['max_stack_depth'])
    print_result("Total Function Calls:", len(result['function_calls']))

    factorial_calls = [c for c in result['function_calls'] if c['function_name'] == 'factorial']
    print(f"\nFactorial Calls (n -> result):")
    for call in factorial_calls:
        n = call['arguments'].get('n', 'N/A')
        ret = call['return_value']
        depth = call['stack_depth']
        print(f"  factorial({n}) = {ret}  [depth: {depth}]")

    print("\nOutput:")
    print(result['stdout'])


def demo_loops():
    """Demo: Loop iteration counting."""
    print_section("Demo 4: Loop Execution Tracking")

    code = """
# Simple for loop
total = 0
for i in range(5):
    total += i

# While loop
count = 0
while count < 3:
    count += 1

# Nested loops
matrix_sum = 0
for i in range(3):
    for j in range(3):
        matrix_sum += i * j
"""

    print("Code:")
    print(code)

    analyzer = DynamicAnalyzer()
    result = analyzer.analyze(code)

    print("\nLoop Executions:")
    for i, loop in enumerate(result['loop_executions'], 1):
        print(f"  Loop {i}:")
        print(f"    Type: {loop['loop_type']}")
        print(f"    Line: {loop['line_start']}")
        print(f"    Iterations: {loop['iteration_count']}")

    print("\nFinal Variables:")
    for var_name, var_info in result['final_variables'].items():
        if 'total' in var_name or 'count' in var_name or 'sum' in var_name:
            print(f"  {var_name}: {var_info['value']}")


def demo_fibonacci():
    """Demo: Complex program with multiple features."""
    print_section("Demo 5: Fibonacci Sequence (Complex Program)")

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
        print(f"F({i}) = {value}")
    return results

numbers = print_fibonacci(7)
print(f"\\nSequence: {numbers}")
"""

    print("Code:")
    print(code)

    analyzer = DynamicAnalyzer()
    result = analyzer.analyze(code)

    print("\nResults:")
    print_result("Execution Successful:", result['execution_successful'])
    print_result("Max Stack Depth:", result['max_stack_depth'])
    print_result("Total Lines Executed:", result['total_lines_executed'])
    print_result("Unique Lines:", result['unique_lines_executed'])

    fib_calls = [c for c in result['function_calls'] if c['function_name'] == 'fibonacci']
    print_result("Fibonacci Calls:", len(fib_calls))

    print_fib_calls = [c for c in result['function_calls'] if c['function_name'] == 'print_fibonacci']
    print_result("Print Fibonacci Calls:", len(print_fib_calls))

    print("\nLoop Executions:")
    for loop in result['loop_executions']:
        print(f"  {loop['loop_type']} loop at line {loop['line_start']}: {loop['iteration_count']} iterations")

    print("\nOutput:")
    print(result['stdout'])


def demo_error_handling():
    """Demo: Exception handling and error reporting."""
    print_section("Demo 6: Error Handling")

    code = """
def divide(a, b):
    return a / b

result1 = divide(10, 2)
print(f"10 / 2 = {result1}")

result2 = divide(10, 0)  # This will raise an error
print("This line won't execute")
"""

    print("Code:")
    print(code)

    analyzer = DynamicAnalyzer()
    result = analyzer.analyze(code)

    print("\nResults:")
    print_result("Execution Successful:", result['execution_successful'])
    print_result("Exception:", result['exception'] or "None")

    print("\nFunction Calls (before error):")
    for call in result['function_calls']:
        args_str = ", ".join(f"{k}={v}" for k, v in call['arguments'].items())
        print(f"  {call['function_name']}({args_str}) -> {call['return_value']}")

    print("\nOutput (before error):")
    print(result['stdout'])


def demo_variable_tracking():
    """Demo: Variable value tracking through execution."""
    print_section("Demo 7: Variable Value Tracking")

    code = """
x = 1
print(f"x = {x}")
x = x * 2
print(f"x = {x}")
x = x + 10
print(f"x = {x}")
x = x ** 2
print(f"x = {x}")
"""

    print("Code:")
    print(code)

    analyzer = DynamicAnalyzer()
    result = analyzer.analyze(code)

    print("\nVariable Snapshots for 'x':")
    x_snapshots = [s for s in result['variable_snapshots'] if s['name'] == 'x']

    # Get unique values by line
    seen_values = set()
    for snapshot in x_snapshots:
        value = snapshot['value']
        if value not in seen_values:
            print(f"  Line {snapshot['line']}: x = {value}")
            seen_values.add(value)

    print("\nOutput:")
    print(result['stdout'])


def main():
    """Run all demos."""
    print("=" * 70)
    print("  DYNAMIC CODE ANALYZER - DEMONSTRATION")
    print("=" * 70)
    print("\nThis demo showcases the capabilities of the Dynamic Code Analyzer.")
    print("The analyzer executes Python code and collects runtime information:")
    print("  - Variable values throughout execution")
    print("  - Function calls with arguments and return values")
    print("  - Loop iteration counts")
    print("  - Call stack depth")
    print("  - Execution flow and line coverage")
    print("  - Output and error handling")

    try:
        demo_simple_execution()
        demo_function_calls()
        demo_recursion()
        demo_loops()
        demo_fibonacci()
        demo_error_handling()
        demo_variable_tracking()

        print_section("Demo Complete!")
        print("\nThe Dynamic Analyzer successfully tracked execution details")
        print("for all test programs. This information can be used to:")
        print("  - Generate questions about variable values at specific lines")
        print("  - Ask about loop iteration counts")
        print("  - Test understanding of recursive call depth")
        print("  - Verify execution flow comprehension")
        print("  - Assess understanding of runtime behavior")

    except Exception as e:
        print(f"\n\nError running demos: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
