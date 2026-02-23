# PRD: LLM-as-a-Judge Evaluation System for QLC

**Project:** QLC – Questions about Learners' Code
**Feature:** On-demand LLM-based question quality evaluation
**Author:** Nicolas Moschenross
**Date:** 2026-02-23
**Status:** Draft

---

## 1. Overview

### 1.1 Problem Statement

The QLC system uses an AI (OpenAI GPT) to generate comprehension questions from student Python code. Currently, there is no mechanism to assess whether those generated questions are actually good — whether the stated correct answers are accurate, whether the questions test real understanding, or whether the difficulty label is appropriate.

Without quality evaluation, generated questions that are wrong, ambiguous, or pedagogically useless are indistinguishable from high-quality ones. This undermines the educational value of the system and makes it difficult to trust the output.

### 1.2 Proposed Solution

An on-demand "LLM-as-a-Judge" evaluation endpoint. After a code submission generates questions, an evaluator can call a separate endpoint to have a second LLM pass review each question against the original code and its analysis data. The judge scores each question on multiple quality dimensions and returns per-question scores, explanations, and a flagging mechanism for low-quality questions.

### 1.3 Goals

- Score every question generated for a submission on 5 pedagogical quality dimensions
- Provide human-readable explanations for every score
- Flag questions that fall below an acceptable quality threshold
- Return aggregate statistics across all questions in a submission
- Keep evaluation separate from generation (on-demand, not automatic) to avoid doubling API costs

### 1.4 Non-Goals

- Automatically re-generating low-quality questions (out of scope for this version)
- Real-time evaluation during question generation
- Fine-tuning or training a custom judge model
- Evaluating student answers (separate concern)

---

## 2. Background & Context

### 2.1 Current System Flow

```
Student submits code
       ↓
POST /api/submit-code
       ↓
Static Analysis + Dynamic Analysis
       ↓
AI Question Generator (GPT) → questions[]
       ↓
Questions returned to student
       ↓
Student submits answers → POST /api/submit-answer
```

### 2.2 Where Judge Fits

```
(After submission exists)

Evaluator calls POST /api/evaluate/{submission_id}
       ↓
LLM Judge reads: code + static analysis + dynamic analysis + questions
       ↓
For each question → scores + explanation + issues[]
       ↓
Returns EvaluationResult with per-question + aggregate data
```

### 2.3 Why On-Demand

- Every evaluation call costs tokens (roughly the same as generating the questions)
- Not every submission needs evaluation (e.g. during live student sessions)
- Evaluation is primarily useful for: research/dissertation analysis, quality monitoring, batch testing sample codes

---

## 3. Functional Requirements

### 3.1 New API Endpoint

```
POST /api/evaluate/{submission_id}
```

**Path Parameters:**
- `submission_id` — ID of an existing submission (from POST /api/submit-code)

**Response:**
- `200 OK` — EvaluationResult JSON
- `404 Not Found` — submission_id does not exist
- `500 Internal Server Error` — judge LLM call failed

**No request body required.** All data needed (code, analysis, questions) is already stored in `submissions_store` from the original submission.

### 3.2 Scoring Dimensions

Each question is scored on 5 dimensions, each on a **1–5 integer scale**:

| Dimension | What the judge assesses | Score 1 | Score 5 |
|-----------|------------------------|---------|---------|
| `accuracy` | Is the stated correct answer verifiably correct based on static/dynamic analysis data? | Answer is wrong or unverifiable | Answer is provably correct from analysis |
| `clarity` | Is the question unambiguous and well-phrased? | Confusing or misleading | Clear, precise, no ambiguity |
| `pedagogical_value` | Does it test genuine understanding vs. trivial recall? | Tests nothing meaningful | Tests deep comprehension |
| `code_specificity` | Is it specific to this code, or generic enough to apply to any code? | Could apply to any Python code | Only makes sense for this specific code |
| `difficulty_calibration` | Does the difficulty label match the actual cognitive demand? | Badly miscalibrated | Perfectly calibrated |

**Overall score:** weighted average — `accuracy` and `pedagogical_value` weighted 2x, others 1x.

```
overall = (accuracy*2 + clarity + pedagogical_value*2 + code_specificity + difficulty_calibration) / 7
```

### 3.3 Flagging

A question is **flagged** if:
- `overall_score < 3.0`, OR
- `accuracy < 3` (wrong answer is never acceptable regardless of other scores)

Flagged questions include an `issues[]` list of plain-English problems identified by the judge (e.g. `"correct_answer contradicts dynamic analysis"`, `"question could apply to any loop, not this specific one"`).

### 3.4 Aggregate Statistics

The evaluation result includes aggregate stats across all questions:

```json
{
  "mean_overall": 3.8,
  "mean_accuracy": 4.1,
  "mean_clarity": 3.9,
  "mean_pedagogical_value": 3.6,
  "mean_code_specificity": 3.4,
  "mean_difficulty_calibration": 3.7,
  "total_questions": 8,
  "questions_flagged": 2,
  "questions_flagged_ids": ["q_abc123", "q_def456"]
}
```

---

## 4. Technical Design

### 4.1 New File: `backend/question_engine/judge.py`

```
LLMJudge
├── __init__(config: JudgeConfig, api_key: str)
├── evaluate_submission(submission_data: dict) → EvaluationResult
├── _evaluate_question(question, code, static_analysis, dynamic_analysis) → QuestionEvaluation
├── _build_judge_prompt(question, code, static_analysis, dynamic_analysis) → str
└── _parse_evaluation(response_text: str) → QuestionEvaluation
```

**Data structures:**

```python
@dataclass
class JudgeConfig:
    model: str = "gpt-4o"          # Separate model from generator
    temperature: float = 0.2        # Low temp for consistent scoring
    max_tokens: int = 1000          # Per question evaluation
    request_timeout: int = 30

@dataclass
class QuestionEvaluation:
    question_id: str
    question_text: str
    scores: Dict[str, int]          # dimension → 1-5
    overall_score: float
    explanation: str                # judge's reasoning
    issues: List[str]               # identified problems
    is_flagged: bool

@dataclass
class EvaluationResult:
    submission_id: str
    question_evaluations: List[QuestionEvaluation]
    aggregate: Dict[str, float]     # mean scores + counts
    tokens_used: int
    evaluation_time_ms: float
```

### 4.2 Judge System Prompt

```
You are a quality evaluator for AI-generated comprehension questions about student code.

You have access to:
1. The student's original Python code
2. Static analysis results (ground truth about code structure)
3. Dynamic analysis results (ground truth about runtime values and behavior)
4. A generated question with its stated correct answer

Your task: score this question on 5 dimensions (1-5 each) and identify any issues.

CRITICAL RULES:
- For ACCURACY: cross-check the correct_answer against dynamic analysis values.
  If the question claims a variable equals X but dynamic analysis shows Y, accuracy = 1.
- For CODE_SPECIFICITY: could this exact question (with this exact answer) be asked
  about any Python program, or does it require knowing THIS specific code?
- Be strict. A score of 5 means the question is genuinely excellent on that dimension.
- A score of 3 is average/acceptable. Below 3 means there is a real problem.

Return JSON with this structure:
{
  "scores": {
    "accuracy": <1-5>,
    "clarity": <1-5>,
    "pedagogical_value": <1-5>,
    "code_specificity": <1-5>,
    "difficulty_calibration": <1-5>
  },
  "explanation": "<one paragraph explaining your scoring>",
  "issues": ["<issue 1>", "<issue 2>"]  // empty list if no issues
}
```

### 4.3 Pydantic Models (additions to `backend/api/models.py`)

```python
class QuestionEvaluationResponse(BaseModel):
    question_id: str
    question_text: str
    scores: Dict[str, int]
    overall_score: float
    explanation: str
    issues: List[str]
    is_flagged: bool

class EvaluationResultResponse(BaseModel):
    submission_id: str
    question_evaluations: List[QuestionEvaluationResponse]
    aggregate: Dict[str, float]
    tokens_used: int
    evaluation_time_ms: float
```

### 4.4 Route Addition (`backend/api/routes.py`)

```python
@router.post(
    "/evaluate/{submission_id}",
    response_model=EvaluationResultResponse,
    tags=["Evaluation"]
)
def evaluate_submission(submission_id: str):
    if submission_id not in submissions_store:
        raise HTTPException(status_code=404, detail="Submission not found")

    submission = submissions_store[submission_id]
    judge = LLMJudge()
    result = judge.evaluate_submission(submission)
    return result
```

### 4.5 Data Flow

```
submissions_store[submission_id] contains:
├── "code"       → passed to judge as context
├── "result"
│   ├── static_analysis   → passed as ground truth
│   └── dynamic_analysis  → passed as ground truth (runtime values)
└── "questions"  → List[Question] to evaluate (one judge call per question)
```

The judge makes **N separate API calls** (one per question). This is intentional — it gives more focused evaluations and avoids the judge being influenced by other questions in the batch.

---

## 5. Sample Evaluation Script (Dissertation Evidence)

`tests/evaluate_sample_codes.py`

Runs a curated set of sample student codes end-to-end and prints a summary table.

**Sample codes to include:**
1. Simple `for` loop accumulating a sum
2. Recursive factorial function
3. Class with `__init__` and methods
4. Nested loops with a 2D list
5. Function with try/except error handling
6. List comprehension
7. While loop with early `break`
8. Fibonacci with memoization

**Output format:**
```
Sample Code: factorial.py
─────────────────────────────────────────────────────
Q1 | accuracy=5 clarity=4 pedagogy=5 specificity=4 diff=4 | overall=4.6 | OK
Q2 | accuracy=5 clarity=5 pedagogy=4 specificity=5 diff=3 | overall=4.4 | OK
Q3 | accuracy=2 clarity=4 pedagogy=3 specificity=3 diff=4 | overall=3.0 | ⚠ FLAGGED
   └─ Issues: "correct_answer contradicts dynamic analysis (expected 120, stated 24)"
─────────────────────────────────────────────────────
Aggregate: mean_overall=4.0 | flagged=1/3
```

This data can be used directly in dissertation findings to quantify question quality.

---

## 6. Implementation Plan

| Step | File | Description | Estimated Size |
|------|------|-------------|----------------|
| 1 | `backend/question_engine/judge.py` | Core judge logic | ~150 lines |
| 2 | `backend/api/models.py` | Add Pydantic response models | ~30 lines |
| 3 | `backend/api/routes.py` | Add evaluate endpoint | ~25 lines |
| 4 | `tests/evaluate_sample_codes.py` | Batch eval script | ~80 lines |

**Total: ~285 lines of new code across 4 files. No existing code needs to change.**

---

## 7. Known Constraints & Risks

| Risk | Mitigation |
|------|-----------|
| Judge model also makes mistakes | Use low temperature (0.2) for consistency; treat scores as heuristics not ground truth |
| N API calls per evaluation (one per question) | Each call is small (~1000 tokens); acceptable for on-demand use |
| Submissions stored in-memory — lost on restart | Evaluate immediately after submission in the same session |
| The judge and generator use the same model | Use a different/cheaper model for judging (e.g. `gpt-4o-mini`) |
| No ground truth to validate judge scores against | Manually validate 10-20 questions for dissertation; use inter-rater agreement as proxy |

---

## 8. Success Criteria

- [ ] `POST /api/evaluate/{submission_id}` returns well-formed JSON for any valid submission
- [ ] Accuracy scores correctly identify at least 80% of manually verified correct/incorrect answers
- [ ] Flagging threshold catches obviously bad questions (tested manually)
- [ ] Batch script runs successfully on all 8 sample codes and produces a readable report
- [ ] API is testable via Swagger UI at `/docs`

---

## 9. Out of Scope (Future Work)

- Storing evaluation results persistently (database)
- Exposing evaluation results to students (currently for evaluator/researcher use only)
- Using evaluation feedback to improve the generator prompt
- A/B testing different judge prompts
- Automated re-generation of flagged questions
