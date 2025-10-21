#!/usr/bin/env python3
"""
Demo: Complete Question Generation Pipeline

Demonstrates the end-to-end question generation system:
1. Student submits code
2. System analyzes code (static + dynamic)
3. System finds applicable templates
4. System generates questions
5. System filters and prioritizes questions
6. Questions are presented to student
"""

import sys
from pathlib import Path
import json

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

from question_engine.generator import (
    QuestionGenerator,
    GenerationConfig,
    GenerationStrategy,
    generate_questions_simple
)
from question_engine.templates import QuestionLevel, QuestionType


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_question(question, index: int):
    """Print a formatted question."""
    print(f"\n┌─ Question {index} ───────────────────────────────────────────────────")
    print(f"│ Level: {question.question_level.value.upper()}")
    print(f"│ Type: {question.question_type.value}")
    print(f"│ Difficulty: {question.difficulty}")
    print(f"│ Template: {question.template_id}")
    print("├" + "─" * 74)
    print(f"│ {question.question_text}")

    if question.answer_choices:
        print("│")
        print("│ Choices:")
        for i, choice in enumerate(question.answer_choices, 1):
            marker = "✓" if choice.is_correct else "○"
            print(f"│   [{marker}] {choice.text}")
    else:
        print("│")
        print(f"│ Expected Answer: {question.correct_answer}")

    if question.explanation:
        print("│")
        print(f"│ Explanation: {question.explanation}")

    print("└" + "─" * 74)


def demo_basic_usage():
    """Demo 1: Basic usage with default settings."""
    print_section("DEMO 1: Basic Usage - Default Settings")

    code = """
def factorial(n):
    '''Calculate factorial recursively'''
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def is_even(num):
    '''Check if a number is even'''
    return num % 2 == 0

# Test the functions
result = factorial(5)
check = is_even(result)
print(f"Factorial of 5 is {result}")
print(f"Is it even? {check}")
"""

    print("Student Code:")
    print("-" * 80)
    print(code)
    print("-" * 80)

    # Generate questions using simplest API
    print("\n[Generating questions with default settings...]")
    questions = generate_questions_simple(code)

    print(f"\n✓ Generated {len(questions)} questions")

    for i, question in enumerate(questions, 1):
        print_question(question, i)


def demo_custom_configuration():
    """Demo 2: Custom configuration."""
    print_section("DEMO 2: Custom Configuration")

    code = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        if not swapped:
            break
    return arr

numbers = [64, 34, 25, 12, 22, 11, 90]
sorted_numbers = bubble_sort(numbers)
print(f"Sorted: {sorted_numbers}")
"""

    print("Student Code:")
    print("-" * 80)
    print(code)
    print("-" * 80)

    # Create custom configuration
    config = GenerationConfig(
        max_questions=5,
        strategy=GenerationStrategy.DIVERSE,
        allowed_levels={QuestionLevel.BLOCK, QuestionLevel.ATOM},
        allowed_difficulties={'easy', 'medium'}
    )

    print("\nConfiguration:")
    print(f"  - Max questions: {config.max_questions}")
    print(f"  - Strategy: {config.strategy.value}")
    print(f"  - Allowed levels: {[l.value for l in config.allowed_levels]}")
    print(f"  - Allowed difficulties: {config.allowed_difficulties}")

    generator = QuestionGenerator(config)
    result = generator.generate(code)

    print(f"\n✓ Generated {result.total_generated} questions")
    print(f"✓ Filtered to {len(result.questions)} questions")
    print(f"✓ Execution time: {result.execution_time_ms:.2f}ms")

    for i, question in enumerate(result.questions, 1):
        print_question(question, i)


def demo_different_strategies():
    """Demo 3: Different selection strategies."""
    print_section("DEMO 3: Question Selection Strategies")

    code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

def fibonacci_iterative(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return b

# Compare implementations
n = 6
recursive_result = fibonacci(n)
iterative_result = fibonacci_iterative(n)
"""

    print("Student Code:")
    print("-" * 80)
    print(code)
    print("-" * 80)

    strategies = [
        (GenerationStrategy.DIVERSE, "Maximize diversity"),
        (GenerationStrategy.FOCUSED, "Focus on specific areas"),
        (GenerationStrategy.ALL, "Return all questions")
    ]

    for strategy, description in strategies:
        print(f"\n─── Strategy: {strategy.value.upper()} ({description}) ───")

        config = GenerationConfig(
            strategy=strategy,
            max_questions=6
        )

        generator = QuestionGenerator(config)
        result = generator.generate(code)

        print(f"Questions generated: {len(result.questions)}")

        # Show question distribution
        from collections import Counter
        levels = Counter(q.question_level.value for q in result.questions)
        types = Counter(q.question_type.value for q in result.questions)

        print(f"  By level: {dict(levels)}")
        print(f"  By type: {dict(types)}")


def demo_error_handling():
    """Demo 4: Error handling."""
    print_section("DEMO 4: Error Handling")

    print("─── Test 1: Syntax Error ───")
    syntax_error_code = """
def broken(
    print("missing closing paren")
"""
    print("Code with syntax error:")
    print(syntax_error_code)

    generator = QuestionGenerator()
    result = generator.generate(syntax_error_code)

    print(f"\nExecution successful: {result.execution_successful}")
    print(f"Questions generated: {len(result.questions)}")
    print(f"Errors: {result.errors}")

    print("\n─── Test 2: Runtime Error ───")
    runtime_error_code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def helper(x):
    return x

result = factorial(5)
crash = 1 / 0  # Division by zero
"""
    print("Code with runtime error:")
    print(runtime_error_code)

    result = generator.generate(runtime_error_code)

    print(f"\nExecution successful: {result.execution_successful}")
    print(f"Static analysis: {'✓' if result.static_analysis else '✗'}")
    print(f"Dynamic analysis: {'✓' if result.dynamic_analysis else '✗'}")
    print(f"Questions generated: {len(result.questions)}")
    print(f"Warnings: {result.warnings}")

    # Still might have questions from static analysis
    if result.questions:
        print("\nQuestions from static analysis:")
        for i, q in enumerate(result.questions[:2], 1):
            print(f"  {i}. {q.question_text}")


def demo_json_output():
    """Demo 5: JSON output for API."""
    print_section("DEMO 5: JSON Output (for REST API)")

    code = """
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

result = gcd(48, 18)
"""

    print("Student Code:")
    print("-" * 80)
    print(code)
    print("-" * 80)

    config = GenerationConfig(max_questions=4)
    generator = QuestionGenerator(config)
    result = generator.generate(code)

    # Convert to JSON
    result_dict = result.to_dict()
    json_output = json.dumps(result_dict, indent=2)

    print("\nJSON Output:")
    print("-" * 80)
    # Print first 1500 chars to keep it readable
    if len(json_output) > 1500:
        print(json_output[:1500])
        print(f"\n... (truncated, total length: {len(json_output)} characters)")
    else:
        print(json_output)
    print("-" * 80)

    print(f"\n✓ JSON is {len(json_output)} characters")
    print(f"✓ Contains {len(result_dict['questions'])} questions")
    print(f"✓ Includes metadata, analysis summaries, and error/warning info")


def demo_filtering():
    """Demo 6: Advanced filtering."""
    print_section("DEMO 6: Advanced Filtering")

    code = """
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

numbers = [3, 6, 8, 10, 1, 2, 1]
sorted_numbers = quick_sort(numbers)
"""

    print("Student Code:")
    print("-" * 80)
    print(code)
    print("-" * 80)

    print("\n─── Filter 1: Only BLOCK level questions ───")
    config1 = GenerationConfig(
        allowed_levels={QuestionLevel.BLOCK},
        max_questions=10
    )
    result1 = QuestionGenerator(config1).generate(code)
    print(f"Questions: {len(result1.questions)}")
    for q in result1.questions:
        print(f"  - {q.question_level.value}: {q.question_text[:60]}...")

    print("\n─── Filter 2: Only easy difficulty ───")
    config2 = GenerationConfig(
        allowed_difficulties={'easy'},
        max_questions=10
    )
    result2 = QuestionGenerator(config2).generate(code)
    print(f"Questions: {len(result2.questions)}")
    for q in result2.questions:
        print(f"  - {q.difficulty}: {q.question_text[:60]}...")

    print("\n─── Filter 3: Only numeric questions ───")
    config3 = GenerationConfig(
        allowed_types={QuestionType.NUMERIC},
        max_questions=10
    )
    result3 = QuestionGenerator(config3).generate(code)
    print(f"Questions: {len(result3.questions)}")
    for q in result3.questions:
        print(f"  - {q.question_type.value}: {q.question_text[:60]}...")


def demo_complete_workflow():
    """Demo 7: Complete workflow simulation."""
    print_section("DEMO 7: Complete Workflow Simulation")

    print("Simulating a complete student interaction...\n")

    # Student writes code
    code = """
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

def find_primes(limit):
    primes = []
    for num in range(2, limit):
        if is_prime(num):
            primes.append(num)
    return primes

result = find_primes(20)
print(f"Primes up to 20: {result}")
"""

    print("1. Student submits code")
    print("-" * 80)
    print(code)
    print("-" * 80)

    # System generates questions
    print("\n2. System analyzes code and generates questions...")
    config = GenerationConfig(max_questions=5, strategy=GenerationStrategy.DIVERSE)
    generator = QuestionGenerator(config)
    result = generator.generate(code)

    print(f"\n3. Analysis complete:")
    print(f"   ✓ Static analysis: {result.static_analysis['summary']['total_functions']} functions, "
          f"{result.static_analysis['summary']['total_loops']} loops")
    print(f"   ✓ Dynamic analysis: Executed {result.dynamic_analysis['total_lines_executed']} lines")
    print(f"   ✓ Generated {result.total_generated} questions")
    print(f"   ✓ Selected {len(result.questions)} diverse questions")

    # Present questions to student
    print("\n4. Questions presented to student:")
    for i, question in enumerate(result.questions, 1):
        print_question(question, i)

    print("\n5. Student answers questions...")
    print("   [Student interaction would happen here]")

    print("\n6. System provides feedback")
    print("   [Feedback based on answers would be shown here]")


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 18 + "QUESTION GENERATION PIPELINE DEMO" + " " * 27 + "║")
    print("╚" + "═" * 78 + "╝")

    try:
        demo_basic_usage()
        demo_custom_configuration()
        demo_different_strategies()
        demo_error_handling()
        demo_json_output()
        demo_filtering()
        demo_complete_workflow()

        print_section("All Demos Complete!")
        print("✓ The Question Generator successfully orchestrates the entire pipeline")
        print("\nKey Features Demonstrated:")
        print("  • Automatic code analysis (static + dynamic)")
        print("  • Template matching and question generation")
        print("  • Flexible configuration and filtering")
        print("  • Multiple selection strategies")
        print("  • Robust error handling")
        print("  • JSON serialization for APIs")
        print("  • Complete end-to-end workflow")
        print("\nNext Steps:")
        print("  • Integrate with REST API backend")
        print("  • Add database persistence")
        print("  • Build React frontend")
        print("  • Implement answer assessment")

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
