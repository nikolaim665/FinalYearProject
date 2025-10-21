#!/usr/bin/env python3
"""
Demo: Question Template System

Demonstrates the question template system by analyzing sample student code
and generating questions about it.
"""

import sys
from pathlib import Path
import json

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

from analyzers.static_analyzer import StaticAnalyzer
from analyzers.dynamic_analyzer import DynamicAnalyzer
from question_engine.templates import get_registry


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_question(question, index: int):
    """Print a formatted question."""
    print(f"\n[Question {index}] ({question.question_level.value.upper()} level)")
    print(f"Template: {question.template_id}")
    print(f"Type: {question.question_type.value}")
    print(f"Difficulty: {question.difficulty}")
    print(f"\n{question.question_text}")

    if question.answer_choices:
        print("\nChoices:")
        for i, choice in enumerate(question.answer_choices, 1):
            marker = "✓" if choice.is_correct else " "
            print(f"  [{marker}] {choice.text}")
    else:
        print(f"\nCorrect Answer: {question.correct_answer}")

    if question.explanation:
        print(f"\nExplanation: {question.explanation}")

    print(f"\nContext: {json.dumps(question.context, indent=2)}")


def demo_simple_recursion():
    """Demo with a simple recursive function."""
    print_section("DEMO 1: Simple Recursive Function")

    code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def double(x):
    return x * 2

result = factorial(5)
doubled = double(10)
"""

    print("Student Code:")
    print("-" * 80)
    print(code)
    print("-" * 80)

    # Analyze
    static_analyzer = StaticAnalyzer()
    dynamic_analyzer = DynamicAnalyzer()

    print("\n[Analyzing code...]")
    static_analysis = static_analyzer.analyze(code)
    dynamic_analysis = dynamic_analyzer.analyze(code)

    print(f"✓ Found {static_analysis['summary']['total_functions']} functions")
    print(f"✓ Found {static_analysis['summary']['total_variables']} variable assignments")
    print(f"✓ Execution {'successful' if dynamic_analysis['execution_successful'] else 'failed'}")
    print(f"✓ Max stack depth: {dynamic_analysis['max_stack_depth']}")

    # Generate questions
    registry = get_registry()
    applicable_templates = registry.get_applicable_templates(static_analysis, dynamic_analysis)

    print(f"\n[Found {len(applicable_templates)} applicable templates]")

    all_questions = []
    for template in applicable_templates:
        questions = template.generate_questions(static_analysis, dynamic_analysis, code)
        all_questions.extend(questions)

    print(f"\n[Generated {len(all_questions)} questions]")

    for i, question in enumerate(all_questions, 1):
        print_question(question, i)


def demo_loops():
    """Demo with loops."""
    print_section("DEMO 2: Loop Iteration Counting")

    code = """
total = 0
for i in range(5):
    total += i

count = 0
while count < 3:
    count += 1

print(f"Total: {total}, Count: {count}")
"""

    print("Student Code:")
    print("-" * 80)
    print(code)
    print("-" * 80)

    # Analyze
    static_analyzer = StaticAnalyzer()
    dynamic_analyzer = DynamicAnalyzer()

    print("\n[Analyzing code...]")
    static_analysis = static_analyzer.analyze(code)
    dynamic_analysis = dynamic_analyzer.analyze(code)

    print(f"✓ Found {static_analysis['summary']['total_loops']} loops")
    print(f"✓ Found {len(dynamic_analysis['loop_executions'])} executed loops")

    # Generate questions
    registry = get_registry()
    applicable_templates = registry.get_applicable_templates(static_analysis, dynamic_analysis)

    all_questions = []
    for template in applicable_templates:
        questions = template.generate_questions(static_analysis, dynamic_analysis, code)
        all_questions.extend(questions)

    print(f"\n[Generated {len(all_questions)} questions]")

    for i, question in enumerate(all_questions, 1):
        print_question(question, i)


def demo_complex_program():
    """Demo with a more complex program."""
    print_section("DEMO 3: Complex Program - Fibonacci")

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

# Compare both implementations
recursive_result = fibonacci(6)
iterative_result = fibonacci_iterative(6)

print(f"Recursive: {recursive_result}")
print(f"Iterative: {iterative_result}")
"""

    print("Student Code:")
    print("-" * 80)
    print(code)
    print("-" * 80)

    # Analyze
    static_analyzer = StaticAnalyzer()
    dynamic_analyzer = DynamicAnalyzer()

    print("\n[Analyzing code...]")
    static_analysis = static_analyzer.analyze(code)
    dynamic_analysis = dynamic_analyzer.analyze(code)

    print(f"✓ Found {static_analysis['summary']['total_functions']} functions")
    print(f"✓ Found {static_analysis['summary']['total_loops']} loops")
    print(f"✓ Has recursion: {static_analysis['summary']['has_recursion']}")
    print(f"✓ Max stack depth: {dynamic_analysis['max_stack_depth']}")
    print(f"✓ Unique lines executed: {dynamic_analysis['unique_lines_executed']}")
    print(f"✓ Total lines executed: {dynamic_analysis['total_lines_executed']}")

    # Generate questions
    registry = get_registry()
    applicable_templates = registry.get_applicable_templates(static_analysis, dynamic_analysis)

    print(f"\n[Found {len(applicable_templates)} applicable templates]")

    all_questions = []
    for template in applicable_templates:
        questions = template.generate_questions(static_analysis, dynamic_analysis, code)
        all_questions.extend(questions)

    print(f"\n[Generated {len(all_questions)} questions]")

    # Group questions by level
    from collections import defaultdict
    questions_by_level = defaultdict(list)
    for question in all_questions:
        questions_by_level[question.question_level.value].append(question)

    question_num = 1
    for level in ['atom', 'block', 'relational', 'macro']:
        if level in questions_by_level:
            print(f"\n--- {level.upper()} LEVEL QUESTIONS ---")
            for question in questions_by_level[level]:
                print_question(question, question_num)
                question_num += 1


def demo_template_registry():
    """Demo the template registry."""
    print_section("DEMO 4: Template Registry")

    registry = get_registry()

    print("Registered Templates:")
    print("-" * 80)

    templates = registry.list_templates()
    for i, template_info in enumerate(templates, 1):
        print(f"\n{i}. {template_info['name']}")
        print(f"   ID: {template_info['id']}")
        print(f"   Description: {template_info['description']}")
        print(f"   Type: {template_info['type']}")
        print(f"   Level: {template_info['level']}")
        print(f"   Difficulty: {template_info['difficulty']}")


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "QUESTION TEMPLATE SYSTEM DEMO" + " " * 28 + "║")
    print("╚" + "═" * 78 + "╝")

    try:
        demo_template_registry()
        demo_simple_recursion()
        demo_loops()
        demo_complex_program()

        print_section("Demo Complete!")
        print("✓ All demos executed successfully")
        print("\nThe Question Template System can:")
        print("  • Identify which templates are applicable to student code")
        print("  • Generate contextual questions about code structure and behavior")
        print("  • Support multiple question types (multiple choice, fill-in, numeric)")
        print("  • Work at different comprehension levels (atom, block, relational, macro)")
        print("  • Combine static and dynamic analysis for rich question generation")

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
