"""
Demo script to showcase the Static Code Analyzer.
Run this to see the analyzer in action with example code.
"""

import sys
from pathlib import Path
import json

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

from analyzers.static_analyzer import StaticAnalyzer


def print_section(title):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def demo_factorial():
    """Demo with a recursive factorial function."""
    print_section("Example 1: Recursive Factorial Function")

    code = """
def factorial(n):
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)

result = factorial(5)
print(f"Factorial of 5 is {result}")
"""

    print("Code:")
    print(code)

    analyzer = StaticAnalyzer()
    result = analyzer.analyze(code)

    print("\nAnalysis Results:")
    print(json.dumps(result, indent=2))


def demo_fibonacci():
    """Demo with Fibonacci sequence."""
    print_section("Example 2: Fibonacci with Loops")

    code = """
def fibonacci(n):
    if n <= 1:
        return n

    a, b = 0, 1
    for i in range(2, n + 1):
        a, b = b, a + b
    return b

def print_fibonacci_sequence(count):
    for i in range(count):
        value = fibonacci(i)
        print(f"F({i}) = {value}")

print_fibonacci_sequence(10)
"""

    print("Code:")
    print(code)

    analyzer = StaticAnalyzer()
    result = analyzer.analyze(code)

    print("\n📊 Summary:")
    summary = result['summary']
    print(f"  - Total Functions: {summary['total_functions']}")
    print(f"  - Total Variables: {summary['total_variables']}")
    print(f"  - Total Loops: {summary['total_loops']}")
    print(f"  - Has Recursion: {summary['has_recursion']}")
    print(f"  - Total Lines: {summary['total_lines']}")

    print("\n🔧 Functions:")
    for func in result['functions']:
        print(f"  - {func['name']}({', '.join(func['params'])})")
        print(f"    ├─ Lines: {func['line_start']}-{func['line_end']}")
        print(f"    ├─ Recursive: {func['is_recursive']}")
        print(f"    ├─ Has Conditionals: {func['has_conditionals']}")
        print(f"    ├─ Has Loops: {func['has_loops']}")
        print(f"    └─ Calls: {', '.join(func['calls_functions']) if func['calls_functions'] else 'None'}")

    print("\n🔁 Loops:")
    for loop in result['loops']:
        loop_var = f" (var: {loop['loop_variable']})" if loop['loop_variable'] else ""
        print(f"  - {loop['type']} loop at line {loop['line_start']}{loop_var}")
        print(f"    └─ Nesting level: {loop['nesting_level']}")


def demo_nested_structure():
    """Demo with nested structures."""
    print_section("Example 3: Nested Loops and Conditionals")

    code = """
def find_pairs(numbers, target):
    pairs = []
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            if numbers[i] + numbers[j] == target:
                pairs.append((numbers[i], numbers[j]))
    return pairs

numbers = [1, 2, 3, 4, 5]
target_sum = 7
result = find_pairs(numbers, target_sum)
print(f"Pairs that sum to {target_sum}: {result}")
"""

    print("Code:")
    print(code)

    analyzer = StaticAnalyzer()
    result = analyzer.analyze(code)

    print("\n🔁 Loop Structure:")
    for i, loop in enumerate(result['loops'], 1):
        indent = "  " * (loop['nesting_level'] + 1)
        print(f"{indent}Loop {i}: {loop['type']} loop (nesting level: {loop['nesting_level']})")
        if loop['loop_variable']:
            print(f"{indent}  └─ Variable: {loop['loop_variable']}")

    print("\n📝 Variables:")
    for var in result['variables']:
        print(f"  - {var['name']} (line {var['line']}, scope: {var['scope']})")


def demo_function_calls():
    """Demo showing function call tracking."""
    print_section("Example 4: Function Call Analysis")

    code = """
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

def calculate(x, y):
    sum_result = add(x, y)
    product = multiply(x, y)
    print(f"Sum: {sum_result}, Product: {product}")
    return sum_result, product

result = calculate(5, 3)
"""

    print("Code:")
    print(code)

    analyzer = StaticAnalyzer()
    result = analyzer.analyze(code)

    print("\n📞 Function Calls:")
    for call in result['function_calls']:
        print(f"  - {call['function']}() called on line {call['line']} with {call['arguments_count']} arguments")

    print("\n🔧 Function Dependencies:")
    for func in result['functions']:
        if func['calls_functions']:
            print(f"  - {func['name']} calls: {', '.join(func['calls_functions'])}")


def main():
    """Run all demos."""
    print("\n" + "🔍" * 30)
    print("  STATIC CODE ANALYZER DEMO")
    print("🔍" * 30)

    demo_factorial()
    demo_fibonacci()
    demo_nested_structure()
    demo_function_calls()

    print_section("Demo Complete!")
    print("\nThe static analyzer successfully extracted:")
    print("  ✓ Function definitions and parameters")
    print("  ✓ Variable declarations and scopes")
    print("  ✓ Loop structures (for/while)")
    print("  ✓ Conditional statements (if/elif/else)")
    print("  ✓ Function calls")
    print("  ✓ Recursion detection")
    print("  ✓ Nested structures")
    print("\nThis data can now be used to generate Questions about Learners' Code!")


if __name__ == "__main__":
    main()
