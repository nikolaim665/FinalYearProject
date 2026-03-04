#!/usr/bin/env python3
"""
Batch Evaluation Script for QLC System — MBPP Edition
======================================================

Pulls the MBPP dataset (374 crowd-sourced beginner Python programs) from
Hugging Face, runs the QLC pipeline on each, evaluates generated questions
with the judge agent, and reports per-sample and aggregate averages.

Usage (on the GCP VM):
    # Via Docker exec (install datasets inside container first):
    sudo docker exec qlc-backend pip install datasets -q
    sudo docker exec qlc-backend python backend/batch_eval.py

    # Limit to first N samples (useful for a quick smoke-test):
    sudo docker exec qlc-backend python backend/batch_eval.py --limit 10

Results are printed to stdout and saved to batch_eval_results.json.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from statistics import mean
from typing import Optional

# ---------------------------------------------------------------------------
# Path / env setup
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR.parent))

from dotenv import load_dotenv
load_dotenv(dotenv_path=BACKEND_DIR.parent / ".env", override=True)

from question_engine.graph import run_pipeline
from question_engine.agents.judge_agent import judge_agent_node

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
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
# MBPP loader
# ---------------------------------------------------------------------------

def load_mbpp_samples(limit: Optional[int] = None) -> list[dict]:
    """
    Load code samples from the MBPP Hugging Face dataset.

    Each MBPP entry has:
        task_id  : int
        text     : natural-language problem description
        code     : the Python solution
        test_list: list of assert statements

    We use `code` directly as the source for QLC.
    """
    try:
        from datasets import load_dataset  # type: ignore
    except ImportError:
        print("ERROR: 'datasets' package not installed.")
        print("  Run: pip install datasets")
        sys.exit(1)

    print("Loading MBPP dataset from Hugging Face...")
    ds = load_dataset("mbpp", split="train", trust_remote_code=True)

    samples = []
    for row in ds:
        code = row.get("code", "").strip()
        if not code:
            continue
        samples.append({
            "label": f"mbpp_{row['task_id']}",
            "code": code,
            "description": row.get("text", ""),
        })
        if limit and len(samples) >= limit:
            break

    print(f"Loaded {len(samples)} MBPP samples.")
    return samples


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def evaluate_state(state: dict) -> Optional[dict]:
    """Return existing evaluation or run the judge agent."""
    if state.get("evaluation"):
        return state["evaluation"]
    result = judge_agent_node(state)
    return result.get("evaluation")


def summarise_evaluation(eval_result: dict) -> dict:
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
    print(f"\n  {'Sample':<28} {label}")
    print(f"  {'Questions':<28} {summary.get('n_questions', '?')} "
          f"(valid: {summary.get('n_valid', '?')})")
    print(f"  {'Overall score':<28} {summary.get('mean_overall', 'N/A')}")
    for dim in SCORE_DIMS:
        print(f"  {dim:<28} {summary.get(f'mean_{dim}', 'N/A')}")
    print(f"  {'Flagged':<28} {summary.get('n_flagged', '?')}/{summary.get('n_questions', '?')}")


def print_questions_and_evals(state: dict, eval_result: dict) -> None:
    """Print each generated question, its answer choices, and judge scores."""
    questions = state.get("questions_complete", [])
    q_evals = {e["question_id"]: e for e in eval_result.get("question_evaluations", [])}

    for idx, q in enumerate(questions, 1):
        q_id = q.get("id", f"q_{idx}")
        flagged = q_evals.get(q_id, {}).get("is_flagged", False)
        flag_mark = " 🚩" if flagged else ""

        print(f"\n  ── Q{idx}{flag_mark} [{q.get('question_level','?').upper()} / "
              f"{q.get('difficulty','?')}] ──────────────────")
        print(f"  {q.get('question_text', '')}")

        for choice in q.get("answer_choices", []):
            marker = "✓" if choice.get("is_correct") else "✗"
            print(f"    {marker} {choice.get('text', '')}")

        ev = q_evals.get(q_id)
        if ev:
            scores = ev.get("scores", {})
            score_str = "  ".join(
                f"{d[:3].upper()}={scores.get(d, '?')}" for d in SCORE_DIMS
            )
            print(f"  Judge: overall={ev.get('overall_score','?')}  |  {score_str}")
            if ev.get("explanation"):
                print(f"  Note : {ev['explanation']}")
            if ev.get("issues"):
                print(f"  Issues: {'; '.join(ev['issues'])}")



# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="QLC batch evaluation using MBPP dataset")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max number of MBPP samples to process (default: all ~374)")
    args = parser.parse_args()

    samples = load_mbpp_samples(limit=args.limit)

    print("=" * 60)
    print("QLC Batch Evaluation — MBPP Dataset")
    print(f"Samples: {len(samples)}  |  Max questions each: {MAX_QUESTIONS_PER_SAMPLE}")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Resume: load any previously completed results so we skip them
    # ------------------------------------------------------------------
    all_results: list[dict] = []
    all_question_evals: list[dict] = []
    already_done: set[str] = set()

    if OUTPUT_FILE.exists():
        try:
            prev = json.loads(OUTPUT_FILE.read_text())
            for rec in prev.get("per_sample", []):
                if "error" not in rec:          # only skip successful ones
                    all_results.append(rec)
                    all_question_evals.extend(rec.get("question_evaluations", []))
                    already_done.add(rec["label"])
            if already_done:
                print(f"Resuming — skipping {len(already_done)} already-completed samples.")
        except Exception:
            pass  # corrupt file; start fresh

    for i, sample in enumerate(samples, 1):
        label = sample["label"]

        if label in already_done:
            print(f"[{i}/{len(samples)}] {label} — already done, skipping.")
            continue

        print(f"\n[{i}/{len(samples)}] {label}")
        if sample.get("description"):
            print(f"  Task: {sample['description'][:80]}...")
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
            print_questions_and_evals(state, eval_result)
            print(f"  Time: {elapsed}s")

            all_results.append({
                "label": label,
                "description": sample.get("description", ""),
                "elapsed_s": elapsed,
                "summary": summary,
                "question_evaluations": eval_result.get("question_evaluations", []),
            })
            all_question_evals.extend(eval_result.get("question_evaluations", []))

        except Exception as exc:
            elapsed = round(time.time() - t0, 1)
            print(f"  ✗ Failed after {elapsed}s: {exc}")
            all_results.append({"label": label, "error": str(exc), "elapsed_s": elapsed})

        # Save incrementally so a crash doesn't lose progress
        _save(all_results, {}, all_question_evals)

    # -----------------------------------------------------------------------
    # Global aggregate
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("GLOBAL AGGREGATE ACROSS ALL SAMPLES")
    print("=" * 60)

    valid_all = [e for e in all_question_evals if e.get("scores")]
    global_summary: dict = {}

    if valid_all:
        global_summary = {
            "n_total_questions": len(all_question_evals),
            "n_valid": len(valid_all),
        }
        for dim in SCORE_DIMS:
            vals = [e["scores"][dim] for e in valid_all if dim in e.get("scores", {})]
            global_summary[f"mean_{dim}"] = round(mean(vals), 2) if vals else None
        overall_vals = [e["overall_score"] for e in valid_all if "overall_score" in e]
        global_summary["mean_overall"] = round(mean(overall_vals), 2) if overall_vals else None
        global_summary["n_flagged"] = sum(1 for e in all_question_evals if e.get("is_flagged"))

        print(f"  Total questions : {global_summary['n_total_questions']} (valid: {global_summary['n_valid']})")
        print(f"  Flagged         : {global_summary['n_flagged']}")
        print(f"  Overall score   : {global_summary.get('mean_overall', 'N/A')}")
        for dim in SCORE_DIMS:
            print(f"  {dim:<30} {global_summary.get(f'mean_{dim}', 'N/A')}")
    else:
        print("  No valid evaluations to aggregate.")

    _save(all_results, global_summary, all_question_evals)
    print(f"\nResults saved to: {OUTPUT_FILE}")
    print("=" * 60)


def _save(per_sample: list, global_summary: dict, all_evals: list) -> None:
    output = {
        "run_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "global_summary": global_summary,
        "per_sample": per_sample,
    }
    OUTPUT_FILE.write_text(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
