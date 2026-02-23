#!/usr/bin/env python3
"""
Batch LLM Judge Evaluation Script

Runs a curated set of sample student codes end-to-end through the QLC pipeline,
then evaluates the generated questions with the LLM judge.

Produces a report table suitable for dissertation findings to quantify question quality.

Usage:
    cd /path/to/FinalYearProject
    python tests/evaluate_sample_codes.py

    # With a custom API key:
    OPENAI_API_KEY=sk-... python tests/evaluate_sample_codes.py

    # Limit to specific samples:
    python tests/evaluate_sample_codes.py --samples factorial nested_loops

    # Save report to file:
    python tests/evaluate_sample_codes.py --output report.txt
"""

import sys
import os
import argparse
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from question_engine.ai_generator import AIQuestionGenerator, GenerationConfig
from question_engine.judge import LLMJudge, JudgeConfig, EvaluationResult

# ---------------------------------------------------------------------------
# Sample student codes
# ---------------------------------------------------------------------------

SAMPLE_CODES: Dict[str, str] = {
    "sum_loop": """\
# Simple for loop accumulating a sum
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
total = 0
for num in numbers:
    total += num
print(total)
""",

    "factorial": """\
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
print(result)
""",

    "class_example": """\
class BankAccount:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance

    def deposit(self, amount):
        self.balance += amount
        return self.balance

    def withdraw(self, amount):
        if amount > self.balance:
            return False
        self.balance -= amount
        return True

    def get_balance(self):
        return self.balance

account = BankAccount("Alice", 100)
account.deposit(50)
account.withdraw(30)
print(account.get_balance())
""",

    "nested_loops": """\
# Nested loops with a 2D list
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
total = 0
for row in matrix:
    for val in row:
        total += val
print(total)
""",

    "try_except": """\
def safe_divide(a, b):
    try:
        result = a / b
        return result
    except ZeroDivisionError:
        return None
    finally:
        print("Division attempted")

print(safe_divide(10, 2))
print(safe_divide(5, 0))
""",

    "list_comprehension": """\
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
evens = [x for x in numbers if x % 2 == 0]
squares = [x ** 2 for x in evens]
print(squares)
""",

    "while_break": """\
# While loop with early break
target = 7
numbers = [1, 3, 5, 7, 9, 11]
found_at = -1
i = 0
while i < len(numbers):
    if numbers[i] == target:
        found_at = i
        break
    i += 1
print(found_at)
""",

    "fibonacci_memo": """\
def fibonacci(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    result = fibonacci(n - 1, memo) + fibonacci(n - 2, memo)
    memo[n] = result
    return result

for i in range(8):
    print(fibonacci(i))
""",
}


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _score_bar(score: int, max_score: int = 5) -> str:
    """Return a visual bar for a score."""
    filled = round(score)
    return "█" * filled + "░" * (max_score - filled)


def _flag_indicator(is_flagged: bool) -> str:
    return "⚠ FLAGGED" if is_flagged else "OK"


def _dim_short(dim: str) -> str:
    mapping = {
        "accuracy": "acc",
        "clarity": "clar",
        "pedagogical_value": "ped",
        "code_specificity": "spec",
        "difficulty_calibration": "diff",
    }
    return mapping.get(dim, dim[:4])


def format_question_line(idx: int, evaluation) -> str:
    """Format a single question evaluation as a compact report line."""
    s = evaluation.scores
    dims = f"acc={s.get('accuracy', 0)} clar={s.get('clarity', 0)} ped={s.get('pedagogical_value', 0)} spec={s.get('code_specificity', 0)} diff={s.get('difficulty_calibration', 0)}"
    flag = _flag_indicator(evaluation.is_flagged)
    return f"Q{idx} | {dims} | overall={evaluation.overall_score:.1f} | {flag}"


def format_issues_lines(evaluation) -> List[str]:
    lines = []
    for issue in evaluation.issues:
        lines.append(f"   └─ Issue: {issue}")
    return lines


def format_sample_report(sample_name: str, eval_result: EvaluationResult) -> str:
    """Format the full report for one sample code."""
    sep = "─" * 65
    lines = [
        f"\nSample Code: {sample_name}",
        sep,
    ]

    for i, ev in enumerate(eval_result.question_evaluations, start=1):
        lines.append(format_question_line(i, ev))
        lines.extend(format_issues_lines(ev))

    agg = eval_result.aggregate
    lines.append(sep)
    lines.append(
        f"Aggregate: mean_overall={agg.get('mean_overall', 0):.2f} | "
        f"mean_accuracy={agg.get('mean_accuracy', 0):.2f} | "
        f"mean_ped={agg.get('mean_pedagogical_value', 0):.2f} | "
        f"flagged={agg.get('questions_flagged', 0)}/{agg.get('total_questions', 0)}"
    )
    lines.append(
        f"Tokens used: {eval_result.tokens_used} | "
        f"Time: {eval_result.evaluation_time_ms:.0f}ms"
    )
    return "\n".join(lines)


def format_summary_table(results: Dict[str, Optional[EvaluationResult]]) -> str:
    """Format an aggregate summary table across all samples."""
    header = (
        f"\n{'='*65}\n"
        f"SUMMARY TABLE\n"
        f"{'='*65}\n"
        f"{'Sample':<22} | {'Overall':>7} | {'Accuracy':>8} | {'Pedagogy':>8} | {'Flagged':>7}\n"
        f"{'-'*65}"
    )
    rows = [header]

    for name, result in results.items():
        if result is None:
            rows.append(f"{name:<22} | {'ERROR':>7} | {'':>8} | {'':>8} | {'':>7}")
            continue
        agg = result.aggregate
        rows.append(
            f"{name:<22} | "
            f"{agg.get('mean_overall', 0):>7.2f} | "
            f"{agg.get('mean_accuracy', 0):>8.2f} | "
            f"{agg.get('mean_pedagogical_value', 0):>8.2f} | "
            f"{agg.get('questions_flagged', 0):>3}/{agg.get('total_questions', 0):<3}"
        )

    rows.append("=" * 65)
    return "\n".join(rows)


# ---------------------------------------------------------------------------
# Main evaluation runner
# ---------------------------------------------------------------------------

def run_evaluation(
    sample_names: Optional[List[str]] = None,
    max_questions: int = 5,
    output_file: Optional[str] = None,
) -> None:
    """
    Run end-to-end evaluation on the curated sample codes.

    Args:
        sample_names: Subset of sample names to run (None = all)
        max_questions: Max questions to generate per sample
        output_file: Path to write report (None = stdout only)
    """
    samples_to_run = sample_names or list(SAMPLE_CODES.keys())
    unknown = [n for n in samples_to_run if n not in SAMPLE_CODES]
    if unknown:
        print(f"Unknown sample names: {unknown}", file=sys.stderr)
        print(f"Available: {list(SAMPLE_CODES.keys())}", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    gen_config = GenerationConfig(max_questions=max_questions)
    judge_config = JudgeConfig()

    generator = AIQuestionGenerator(gen_config, api_key=api_key)
    judge = LLMJudge(judge_config, api_key=api_key)

    report_lines = [
        "=" * 65,
        "QLC LLM JUDGE BATCH EVALUATION REPORT",
        f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Samples: {len(samples_to_run)} | Max questions each: {max_questions}",
        "=" * 65,
    ]

    results: Dict[str, Optional[EvaluationResult]] = {}

    for sample_name in samples_to_run:
        code = SAMPLE_CODES[sample_name]
        print(f"\n[{sample_name}] Generating questions...", end=" ", flush=True)

        try:
            gen_result = generator.generate(code)
            n_questions = len(gen_result.questions)
            print(f"Got {n_questions} questions.", end=" ", flush=True)

            if n_questions == 0:
                print("Skipping evaluation (no questions generated).")
                results[sample_name] = None
                report_lines.append(f"\nSample Code: {sample_name}\n  [No questions generated]")
                continue

            print("Evaluating...", end=" ", flush=True)

            # Build submission_data dict (mimicking submissions_store format)
            # Convert GeneratedQuestion objects to minimal API-like objects
            class _QProxy:
                """Thin proxy to expose the fields judge expects."""
                def __init__(self, q, q_id):
                    self.id = q_id
                    self.question_text = q.question_text
                    self.correct_answer = q.correct_answer
                    self.question_type = q.question_type.value if hasattr(q.question_type, 'value') else str(q.question_type)
                    self.question_level = q.question_level.value if hasattr(q.question_level, 'value') else str(q.question_level)
                    self.difficulty = q.difficulty
                    self.answer_choices = q.answer_choices

            proxied_questions = [
                _QProxy(q, f"q_{i+1:02d}") for i, q in enumerate(gen_result.questions)
            ]

            submission_data = {
                "submission_id": f"batch_{sample_name}",
                "code": code,
                "questions": proxied_questions,
                "result": gen_result,
            }

            eval_result = judge.evaluate_submission(submission_data)
            results[sample_name] = eval_result

            agg = eval_result.aggregate
            flagged = agg.get("questions_flagged", 0)
            total = agg.get("total_questions", 0)
            overall = agg.get("mean_overall", 0)
            print(f"Done. overall={overall:.2f}, flagged={flagged}/{total}")

            report_lines.append(format_sample_report(sample_name, eval_result))

        except KeyboardInterrupt:
            print("\nInterrupted by user.")
            break
        except Exception as e:
            print(f"ERROR: {e}")
            results[sample_name] = None
            report_lines.append(f"\nSample Code: {sample_name}\n  [ERROR: {e}]")

    # Append summary table
    report_lines.append(format_summary_table(results))

    report = "\n".join(report_lines)
    print("\n" + report)

    if output_file:
        Path(output_file).write_text(report)
        print(f"\nReport written to: {output_file}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Batch LLM Judge evaluation for QLC sample codes"
    )
    parser.add_argument(
        "--samples",
        nargs="+",
        metavar="NAME",
        help=f"Sample names to run. Available: {list(SAMPLE_CODES.keys())}",
    )
    parser.add_argument(
        "--max-questions",
        type=int,
        default=5,
        help="Max questions to generate per sample (default: 5)",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Write report to this file (in addition to stdout)",
    )
    args = parser.parse_args()

    run_evaluation(
        sample_names=args.samples,
        max_questions=args.max_questions,
        output_file=args.output,
    )


if __name__ == "__main__":
    main()
