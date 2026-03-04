#!/usr/bin/env python3
"""
Batch Evaluation Script for QLC System
=======================================

Runs the QLC pipeline on a set of sample Python snippets, evaluates all
generated questions with the judge agent, and reports per-sample and
aggregate averages across the whole run.

Usage (on the GCP VM, inside the project root):
    # Option A — via Docker exec (no extra deps needed):
    sudo docker exec qlc-backend python backend/batch_eval.py

    # Option B — directly (with venv activated):
    python backend/batch_eval.py

Results are printed to stdout and saved to batch_eval_results.json.
"""

import json
import sys
import time
from pathlib import Path
from statistics import mean
from typing import Optional

# ---------------------------------------------------------------------------
# Add backend to path so imports work when run directly
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR.parent))

# Load .env so OPENAI_API_KEY etc. are available
from dotenv import load_dotenv
load_dotenv(dotenv_path=BACKEND_DIR.parent / ".env", override=True)

from question_engine.graph import run_pipeline
from question_engine.agents.judge_agent import judge_agent_node

# ---------------------------------------------------------------------------
# Sample code snippets to evaluate
# Add / remove entries as needed.
# ---------------------------------------------------------------------------
SAMPLE_CODES = []

MAX_QUESTIONS_PER_SAMPLE = 5
OUTPUT_FILE = BACKEND_DIR.parent / "batch_eval_results.json"

SCORE_DIMS = [
    "accuracy",
    "clarity",
    "pedagogical_value",
    "code_specificity",
    "difficulty_calibration",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def evaluate_state(state: dict) -> Optional[dict]:
    """Run judge agent if not already evaluated."""
    if state.get("evaluation"):
        return state["evaluation"]
    result = judge_agent_node(state)
    return result.get("evaluation")


def summarise_evaluation(eval_result: dict) -> dict:
    """Extract per-dimension means and overall mean from an evaluation dict."""
    question_evals = eval_result.get("question_evaluations", [])
    valid = [e for e in question_evals if e.get("scores")]
    if not valid:
        return {}

    summary: dict = {"n_questions": len(question_evals), "n_valid": len(valid)}
    for dim in SCORE_DIMS:
        vals = [e["scores"][dim] for e in valid if dim in e.get("scores", {})]
        summary[f"mean_{dim}"] = round(mean(vals), 2) if vals else None

    overall_vals = [e["overall_score"] for e in valid if "overall_score" in e]
    summary["mean_overall"] = round(mean(overall_vals), 2) if overall_vals else None
    summary["n_flagged"] = sum(1 for e in question_evals if e.get("is_flagged"))
    return summary


def print_summary(label: str, summary: dict) -> None:
    flagged_info = f"  Flagged: {summary.get('n_flagged', '?')}/{summary.get('n_questions', '?')}"
    print(f"\n  {'Sample':<28} {label}")
    print(f"  {'Questions generated':<28} {summary.get('n_questions', '?')} "
          f"(valid: {summary.get('n_valid', '?')})")
    print(f"  {'Overall score':<28} {summary.get('mean_overall', 'N/A')}")
    for dim in SCORE_DIMS:
        print(f"  {dim:<28} {summary.get(f'mean_{dim}', 'N/A')}")
    print(flagged_info)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("QLC Batch Evaluation")
    print(f"Samples: {len(SAMPLE_CODES)}  |  Max questions each: {MAX_QUESTIONS_PER_SAMPLE}")
    print("=" * 60)

    all_results = []
    all_question_evals: list[dict] = []

    for i, sample in enumerate(SAMPLE_CODES, 1):
        label = sample["label"]
        print(f"\n[{i}/{len(SAMPLE_CODES)}] Running pipeline for: {label} ...")
        t0 = time.time()

        try:
            state = run_pipeline(
                source_code=sample["code"],
                max_questions=MAX_QUESTIONS_PER_SAMPLE,
            )

            eval_result = evaluate_state(state)
            elapsed = round(time.time() - t0, 1)

            if not eval_result:
                print(f"  ⚠ No evaluation produced ({elapsed}s)")
                all_results.append({"label": label, "error": "no evaluation", "elapsed_s": elapsed})
                continue

            summary = summarise_evaluation(eval_result)
            print_summary(label, summary)
            print(f"  Time: {elapsed}s")

            record = {
                "label": label,
                "elapsed_s": elapsed,
                "summary": summary,
                "question_evaluations": eval_result.get("question_evaluations", []),
            }
            all_results.append(record)
            all_question_evals.extend(eval_result.get("question_evaluations", []))

        except Exception as exc:
            elapsed = round(time.time() - t0, 1)
            print(f"  ✗ Failed after {elapsed}s: {exc}")
            all_results.append({"label": label, "error": str(exc), "elapsed_s": elapsed})

    # -----------------------------------------------------------------------
    # Global aggregate across all samples
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("GLOBAL AGGREGATE ACROSS ALL SAMPLES")
    print("=" * 60)

    valid_all = [e for e in all_question_evals if e.get("scores")]
    if valid_all:
        global_summary: dict = {"n_total_questions": len(all_question_evals), "n_valid": len(valid_all)}
        for dim in SCORE_DIMS:
            vals = [e["scores"][dim] for e in valid_all if dim in e.get("scores", {})]
            global_summary[f"mean_{dim}"] = round(mean(vals), 2) if vals else None
        overall_vals = [e["overall_score"] for e in valid_all if "overall_score" in e]
        global_summary["mean_overall"] = round(mean(overall_vals), 2) if overall_vals else None
        global_summary["n_flagged"] = sum(1 for e in all_question_evals if e.get("is_flagged"))

        print(f"  Total questions: {global_summary['n_total_questions']} (valid: {global_summary['n_valid']})")
        print(f"  Flagged:         {global_summary['n_flagged']}")
        print(f"  Overall score:   {global_summary.get('mean_overall', 'N/A')}")
        for dim in SCORE_DIMS:
            print(f"  {dim:<30} {global_summary.get(f'mean_{dim}', 'N/A')}")
    else:
        global_summary = {}
        print("  No valid evaluations to aggregate.")

    # -----------------------------------------------------------------------
    # Save results to JSON
    # -----------------------------------------------------------------------
    output = {
        "run_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "global_summary": global_summary,
        "per_sample": all_results,
    }
    OUTPUT_FILE.write_text(json.dumps(output, indent=2))
    print(f"\nResults saved to: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
