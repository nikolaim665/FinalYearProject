# QLC: Questions about Learners' Code
## Final Year Project — Report Briefing Document

> **Purpose**: This document is a structured briefing for use with AI-assisted deep research and report drafting. It describes the full scope, design decisions, implementation, and evaluation of the QLC system, intended as a skeleton for a Final Year thesis report.

---

## 1. Project Overview and Motivation

### 1.1 Problem Statement

A well-documented challenge in computer science education is that students often produce working code without a deep understanding of why it works. Programs may pass automated tests while the student holds fundamental misconceptions about data types, control flow, or algorithmic behaviour. Traditional formative assessment — lab exercises, code reviews — is costly to scale and does not provide immediate, personalised feedback.

### 1.2 Research Foundation

This project is grounded in the work of **Lehtinen, Santos, and Sorva (2021)**: *"Let's Ask Students About Their Programs, Automatically"* (arXiv:2103.11138). The paper establishes a theoretical and empirical basis for asking students targeted comprehension questions about their own submitted code. Key findings:

- Students who answer code-specific questions demonstrate **significantly better conceptual understanding** than those who receive only test-pass/fail feedback.
- Questions need to be **code-specific** (not generic Python trivia) to be effective.
- Questions should span **multiple cognitive levels**, from surface-level element identification to whole-program understanding.
- The **Block Model** cognitive taxonomy (ATOM → BLOCK → RELATIONAL → MACRO) provides a principled hierarchy for question design.

### 1.3 Project Goal

**QLC (Questions about Learners' Code)** automates the pipeline described in Lehtinen et al.: given a student's Python program, the system performs deep code analysis and uses large language models to generate high-quality, pedagogically grounded multiple-choice questions, complete with distractors targeting known misconceptions and explanations supporting learning.

The system is delivered as a **web application** with a code editor interface, enabling students to submit code and immediately engage with generated questions.

---

## 2. Cognitive Model: The Block Model Taxonomy

The Block Model, as adapted from Lehtinen et al., provides the foundation for question categorisation:

| Level | Cognitive Demand | Focus Area | Example Question |
|-------|-----------------|------------|-----------------|
| **ATOM** | Low | Individual language elements: variable values, types, operators | "What is the type of `arr` after line 3?" |
| **BLOCK** | Low–Medium | Code sections: loop iteration counts, conditional branches, function return values | "How many times does this `for` loop execute?" |
| **RELATIONAL** | Medium–High | Connections between code components: call chains, data flow, scope interactions | "What value does `helper()` pass back to `main()`?" |
| **MACRO** | High | Whole-program understanding: algorithm identity, complexity, overall behaviour | "What sorting algorithm does this implement, and why does it terminate?" |

The QLC system explicitly labels each generated question with its Block Model level and attempts to generate a cognitively diverse set across levels for each submission.

---

## 3. System Architecture

### 3.1 High-Level Components

The system consists of three major components:

1. **Frontend** — React 19 + Vite web application with a Monaco code editor (the same engine as VS Code), question display, answer feedback, and evaluation panels.
2. **Backend** — FastAPI REST API backed by a **LangGraph multi-agent pipeline** that orchestrates code analysis and LLM-driven question generation.
3. **Database** — SQLite via SQLAlchemy, persisting submissions, generated questions, and answer choices.

### 3.2 Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite, TypeScript, Tailwind CSS, Monaco Editor, Lucide Icons |
| Backend API | Python 3.10+, FastAPI, Pydantic v2 |
| Agent Orchestration | LangGraph (StateGraph), LangChain |
| LLM Provider | OpenAI (gpt-4o, gpt-4o-mini) |
| Code Analysis | Python `ast` module (static), `sys.settrace` (dynamic) |
| RAG / Embeddings | FAISS (in-memory), OpenAI `text-embedding-3-small` |
| Database | SQLite, SQLAlchemy 2.0 (DeclarativeBase, sync sessions) |
| Testing | pytest, GitHub Actions CI |
| Deployment | Docker Compose with named volume for DB persistence |

### 3.3 LangGraph Multi-Agent Pipeline

The core intelligence of QLC is implemented as a **LangGraph `StateGraph`**, a directed acyclic graph where each node is an LLM-powered agent or deterministic function. This replaces an earlier monolithic generation approach.

The graph is defined in `backend/question_engine/graph.py` with the following topology:

```
START
  └─→ route_rag (conditional)
        ├─ lecture_slides present → rag_retrieve → analyzer_agent
        └─ no slides              →               analyzer_agent
                                                       │
                                               check_analysis_success (conditional)
                                               ├─ both failed → error_terminal → END
                                               └─ ok          → question_agent
                                                                      │
                                                               answer_agent
                                                                      │
                                                           explanation_agent
                                                                      │
                                                            format_response
                                                                      │
                                                             judge_agent
                                                                      │
                                                                    END
```

**Rationale for LangGraph**: The framework enforces explicit, testable state transitions. Each agent receives a well-defined input (the `QLCState` TypedDict) and produces a well-defined output update. This is superior to monolithic generation for debuggability, modularity, and unit testing (agents can be tested with mocked LLMs).

### 3.4 Shared State: QLCState

All agents communicate through a single `QLCState` TypedDict (defined in `backend/question_engine/state.py`), which accumulates data as it flows through the pipeline:

```python
# Inputs
source_code: str
lecture_slides: Optional[str]
max_questions: int
config: dict                       # model assignments, feature flags

# Populated by RAG node
rag_context: Optional[str]

# Populated by Analyzer Agent
static_analysis: Optional[dict]
dynamic_analysis: Optional[dict]
analysis_warnings: List[str]
analysis_errors: List[str]

# Populated by Question Agent
questions: List[dict]              # question text + metadata only

# Populated by Answer Agent
questions_with_answers: List[dict] # + correct answer + 3 distractors

# Populated by Explanation Agent
questions_complete: List[dict]     # + per-distractor explanations

# Populated by Judge Agent
evaluation: Optional[dict]         # scores on 5 pedagogical dimensions

# Metadata
tokens_used: int
execution_time_ms: float
from_cache: bool
```

---

## 4. Code Analysis

Before any LLM is invoked, QLC performs deep analysis of the student's code using two complementary analysis engines.

### 4.1 Static Analysis (AST-Based)

**File**: `backend/analyzers/static_analyzer.py`

Implemented using Python's `ast` module, which parses source code into an Abstract Syntax Tree without executing it. The analysis is therefore deterministic and always succeeds on syntactically valid code.

**Extracted Information**:
- **Functions**: name, parameters, line range, is_recursive, has_loops, has_conditionals, calls_functions, cyclomatic complexity, is_async, is_generator, decorators, docstring, return type annotations.
- **Classes**: name, base classes, methods, class/instance variables, is_dataclass flag.
- **Variables**: name, scope (global/function/class), type annotation, is_constant (UPPER_CASE detection).
- **Loops**: type (for/while), loop variable, nesting level, iterable type (range/list/generator/etc.), has_break, has_continue, has_else.
- **Conditionals**: has_elif, has_else, is_ternary.
- **Function calls**: object.method() detection, argument count, keyword argument names.
- **Comprehensions, context managers, exception handlers, imports**.
- **Summary flags**: has_recursion, has_async, has_classes, total counts per category.

### 4.2 Dynamic Analysis (Execution Tracing)

**File**: `backend/analyzers/dynamic_analyzer.py`

Implemented using `sys.settrace()`, Python's built-in execution hook, which fires a callback on every **call**, **line**, **return**, and **exception** event during execution.

**Extracted Information**:
- **Variable snapshots**: (name, value, type, line, scope) captured at each executed line.
- **Final variable states**: the last observed value of each variable.
- **Function call records**: arguments, return values, stack depth, is_recursive_call.
- **Loop iteration counts**: matched to AST loop objects by line number.
- **Linear execution flow**: ordered list of executed line numbers (up to 1000 entries).
- **stdout/stderr**: captured up to 10KB.
- **Exception information**: exception type, message, traceback.
- **Metadata**: execution_successful, execution_time_ms, memory_peak_mb, timed_out.

**Safety Measures**:
- **5-second timeout** via `ThreadPoolExecutor` — prevents infinite loops from blocking the server.
- **Memory accounting** via `resource.getrusage`.
- **Snapshot limits**: max 1000 variable snapshots, 5000 flow entries, 500 function calls — prevents memory explosion on complex code.
- **Safe serialisation**: complex objects truncated to 1000 characters; deeply nested structures flattened.

### 4.3 Auto Test Driver Generation

A significant challenge arises when student code defines functions but contains no top-level calls — common for library-style submissions. Without execution, dynamic analysis produces no runtime data.

The Analyzer Agent automatically detects this case (functions defined, no top-level calls) and invokes a sub-LLM call (gpt-4o-mini) to generate a minimal test driver:

```python
try:
    _qlc_r1 = factorial(5)
except Exception:
    pass
```

This driver is appended to the code before dynamic analysis, enabling execution tracing. The generation is logged as an analysis warning so it is transparent in the response.

### 4.4 Complementarity of Static and Dynamic Analysis

The two analyses are complementary:

| Capability | Static Analysis | Dynamic Analysis |
|-----------|----------------|-----------------|
| Code structure (functions, loops) | ✓ | ✗ |
| Runtime variable values | ✗ | ✓ |
| Actual loop iteration counts | ✗ | ✓ |
| Recursion detection | ✓ (structural) | ✓ (actual depth) |
| Works on all valid code | ✓ | Only if executable |
| Handles infinite loops | ✓ | ✗ (timeout kills) |

The pipeline proceeds if at least one analysis succeeds; both failing only occurs on severely broken code.

---

## 5. Agent Design

### 5.1 Analyzer Agent

**Model**: `gpt-4o-mini` | **Temperature**: N/A (tool-use, low creativity needed)

This agent acts as an orchestrator, invoking the static and dynamic analysis tools via the LangChain `@tool` interface and collecting results into `QLCState`. It determines when auto test driver generation is needed and triggers it as a sub-call.

**Key Design Decision**: Using an LLM here (rather than deterministic code) allows the agent to reason about whether dynamic analysis results are meaningful, flag anomalies (e.g., execution succeeded but produced no variable data), and generate the test driver with appropriate test cases for the specific function signatures found.

### 5.2 Question Agent

**Model**: `gpt-4o` | **Temperature**: 0.7 (encourages diverse question formulation)

This agent receives compact JSON summaries of the analysis results (top 10 functions, 15 variables, 10 loops — to manage context length) and generates **question text only** — no answers are produced at this stage. This separation is intentional: the Answer Agent has access to full analysis data for answer verification.

**Prompt Strategy**:
- System prompt frames the agent as a "computer science educator specialising in student code comprehension".
- Explicitly instructed on the ATOM/BLOCK/RELATIONAL/MACRO taxonomy with examples.
- Instructed to generate questions at mixed levels unless `include_levels` filter is set.
- If RAG context is present, instructed to align questions with lecture topics.
- Output format: JSON array with `question_text`, `question_type`, `question_level`, `difficulty`, `context` (line_number, variable_name, function_name, data_type), `template_id`.

**Design Decision — Separation of Question and Answer Generation**: Generating questions and answers in a single pass risks the model self-confirming incorrect answers. By separating the agents, the Answer Agent independently verifies the correct answer against the analysis data before generating distractors, improving accuracy.

### 5.3 Answer Agent

**Model**: `gpt-4o` | **Temperature**: 0.5 (balanced creativity and accuracy)

Receives each question from the Question Agent plus the full analysis data. For each question, generates:
- **1 correct answer** — verified against static/dynamic analysis where possible (e.g., confirmed from execution trace, loop count, or variable snapshot).
- **3 distractor answers** — plausible wrong answers explicitly targeting documented misconceptions.

**Distractor Design Philosophy (Misconception Targeting)**:
Distractors are not arbitrary wrong answers; each targets a specific, documentable misconception:
- Off-by-one errors (loop count is 4, not 5)
- Variable reference confusion (confusing `x` with `y` in similar names)
- Type confusion (returning string vs. integer)
- Scope confusion (local vs. global variable)
- Recursion misunderstanding (base case vs. recursive case)
- Boundary condition errors (< vs. <=)

Each distractor includes a `misconception_targeted` field, which is later used by the Explanation Agent.

### 5.4 Explanation Agent

**Model**: `gpt-4o-mini` | **Temperature**: 0.3 (consistency over creativity)

For each question's complete answer set, generates:
- A 2–3 sentence explanation of **why the correct answer is correct**, referencing specific lines/variables from the code.
- For each distractor: **why it is wrong** and what misconception it reveals.
- An optional **learning tip** to help students avoid the misconception in future.

**Rationale**: Research shows that explaining why distractors are wrong (not just marking them incorrect) significantly improves learning outcomes. This agent operationalises that finding at scale.

### 5.5 Judge Agent

**Model**: `gpt-4o` | **Temperature**: 0.1 (deterministic, careful evaluation)

An independent quality-control agent that evaluates every generated question on five pedagogical dimensions, each scored 1–5:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Accuracy** | 2× | Is the stated correct answer verifiably correct per the code and analysis? |
| **Clarity** | 1× | Is the question unambiguous and well-phrased? |
| **Pedagogical Value** | 2× | Does the question reveal genuine understanding, not surface memorisation? |
| **Code Specificity** | 1× | Must the student know *this* code to answer, not generic Python knowledge? |
| **Difficulty Calibration** | 1× | Does the stated difficulty accurately reflect cognitive demand? |

**Overall Score Formula**:
```
overall = (accuracy×2 + clarity×1 + pedagogical_value×2 + code_specificity×1 + difficulty_calibration×1) / 7
```

Accuracy and pedagogical value are double-weighted because an inaccurate question is actively harmful, and a low-value question wastes the student's time.

**Flagging**: Any question with `overall_score < 3.0` OR `accuracy < 3` is flagged, indicating it should be reviewed before use.

**Aggregate statistics** computed across all questions: mean per-dimension scores, flag count, overall quality rating.

---

## 6. RAG Pipeline for Lecture Slides

**File**: `backend/question_engine/rag.py`

When a user provides lecture slide content alongside their code submission, QLC uses **Retrieval-Augmented Generation** to align questions with course material.

**Pipeline**:
1. **Chunking**: Lecture text split using `RecursiveCharacterTextSplitter` (chunk_size=1000, overlap=200 characters).
2. **Embedding**: Each chunk embedded with OpenAI's `text-embedding-3-small` model.
3. **Indexing**: An ephemeral FAISS vector store built in memory (discarded after the request — not persisted).
4. **Querying**: The student's code summary (first 500 characters) used as the query vector.
5. **Retrieval**: Top-3 most semantically similar chunks retrieved.
6. **Injection**: Retrieved chunks concatenated and passed to the Question Agent as `rag_context`.

**Design Decision — Ephemeral Index**: Rather than maintaining a persistent index, the FAISS store is rebuilt per-request. This trades compute cost for simplicity and avoids stale index issues when lecture content changes. For a production system with high request volume, a persistent index with versioning would be preferable.

---

## 7. Answer Validation

**File**: `backend/question_engine/answer_validator.py`

When a student submits an answer, validation goes beyond simple string equality:

| Match Type | Method |
|-----------|--------|
| **EXACT** | Case-sensitive string comparison |
| **NORMALIZED** | Lowercase + whitespace normalisation |
| **ALTERNATIVE** | Synonym expansion (e.g., "loop" ≈ "iteration" ≈ "repetition") |
| **PARTIAL** | Word-overlap after stop-word filtering |
| **NUMERIC_EXACT** | Integer/float equality |
| **NUMERIC_TOLERANCE** | `|student − correct| < tolerance` |
| **NUMERIC_RANGE** | `min ≤ student ≤ max` |
| **NO_MATCH** | All methods failed |

The validator encodes a domain-specific synonym dictionary for programming terminology, preventing students from being marked incorrect for semantically equivalent phrasing.

---

## 8. Frontend

**Stack**: React 19, Vite, TypeScript, Tailwind CSS, Monaco Editor, Lucide Icons

### Key Components

**`CodeEditor.tsx`**: Monaco editor (the VS Code engine) configured for Python. Includes controls for max_questions (1–10), strategy hints, test inputs, and an optional lecture slides paste area. Font size controls and collapsible advanced options improve usability.

**`QuestionPanel.tsx`**: Carousel-style display of questions. Multiple-choice radio buttons, answer submission, immediate feedback with colour-coded correct/incorrect states, progress bar (X of Y answered), and expandable explanation panels.

**`ResultsSummary.tsx`**: Displays the output of code analysis — function count, variable count, loop count, recursion detection, execution time, complexity metrics.

**`EvaluationPanel.tsx`**: Displays Judge Agent scores. Per-question scores on five dimensions with visual indicators. Aggregate statistics and flagged question alerts.

**`ThemeContext.tsx`**: Dark/light mode with localStorage persistence.

---

## 9. REST API

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/submit-code` | Submit code (+ optional slides), run pipeline, return questions |
| `POST` | `/api/submit-answer` | Submit student answer, get correctness + explanation |
| `GET` | `/api/submission/{id}` | Retrieve a stored submission |
| `POST` | `/api/evaluate/{id}` | Return judge evaluation for a submission |
| `GET` | `/api/health` | Health check |
| `GET` | `/api/templates` | Pipeline metadata and available templates |

**`CodeSubmissionRequest`** notably includes `lecture_slides: Optional[str]`, enabling RAG augmentation transparently through the API.

---

## 10. Database

Three tables, created automatically on startup (no migrations framework):

| Table | Key Columns |
|-------|------------|
| `submissions` | `id` (UUID), `code`, `created_at`, `execution_time_ms`, `total_questions`, `errors` |
| `questions` | `id`, `submission_id` (FK), `question_text`, `question_type`, `question_level`, `correct_answer`, `difficulty` |
| `answer_choices` | `id`, `question_id` (FK), `text`, `is_correct`, `explanation` |

Each submission contains N questions; each question contains exactly 4 answer choices (1 correct + 3 distractors). Explanations are stored per answer choice.

---

## 11. Caching

**Mechanism**: In-memory Python dictionary keyed by `SHA256(code + max_questions + filters)`.

**TTL**: 3600 seconds (1 hour).

**Effect**: Identical repeat submissions return instantly without LLM calls. The cache key is deterministic so students can re-load their results.

**Limitation**: Cache is lost on server restart and does not survive horizontal scaling (would require Redis or a persistent cache layer in a production deployment).

---

## 12. Configuration System

The `config` dict passed into `run_pipeline()` controls model assignments and feature flags:

| Key | Default | Description |
|-----|---------|-------------|
| `question_model` | `gpt-4o` | Model for Question Agent |
| `answer_model` | `gpt-4o` | Model for Answer Agent |
| `explanation_model` | `gpt-4o-mini` | Model for Explanation Agent |
| `judge_model` | `gpt-4o` | Model for Judge Agent |
| `driver_model` | `gpt-4o-mini` | Model for Auto Test Driver generation |
| `enable_auto_driver` | `True` | Generate test driver when no top-level calls detected |
| `enable_caching` | `True` | Use in-memory result cache |
| `include_levels` | `[]` | Filter: only generate at these Block Model levels |
| `include_difficulties` | `[]` | Filter: only generate at these difficulties |

This separation of configuration from code enables experimentation: swapping gpt-4o for gpt-4o-mini on the question agent (to compare quality vs. cost) requires no code changes.

---

## 13. Testing

**Framework**: pytest | **CI**: GitHub Actions (Python 3.10, 3.11, 3.12)

| Test File | Count | Coverage Area |
|-----------|-------|--------------|
| `test_answer_validator.py` | 23 | Semantic validation: exact, normalised, synonym, numeric, partial match |
| `test_state.py` | 4 | QLCState initialisation and field defaults |
| `test_tools.py` | 10 (1 skip) | Static and dynamic analyser tool wrappers; skipped: infinite loop timeout |
| `test_graph.py` | 26 | Graph routing, caching behaviour, agent nodes (mocked LLMs), error paths |

**Total**: 63 passing, 1 skipped.

**Agent Testing Strategy**: LangGraph agent nodes are tested with mocked LLM responses using `unittest.mock.patch`. This decouples tests from OpenAI API availability and cost, while still exercising prompt construction, state mutation, and output parsing logic.

**CI Checks**: black, isort, flake8 linting; security scanning via bandit/safety.

---

## 14. Deployment

**Docker Compose** configuration provides a one-command deployment:
- `qlc-backend` container: FastAPI server with all Python dependencies.
- Database persisted via Docker named volume `qlc_data` mounted at `/data/qlc.db`.
- `OPENAI_API_KEY` injected via `.env` file.
- Frontend built statically and served, or run as separate dev server on port 3000.

```bash
# Production
docker compose up --build

# Development
cd backend && uvicorn api.app:app --reload --port 8000
cd frontend && npm run dev
```

---

## 15. Key Design Decisions and Tradeoffs

| Decision | Rationale | Tradeoff |
|----------|-----------|----------|
| **LangGraph pipeline over monolithic generation** | Testable, debuggable, modular; each stage independently inspectable | More LLM calls (5–6 per submission), higher latency (10–30 seconds) |
| **Separate Question and Answer agents** | Prevents self-confirming errors; Answer Agent independently verifies against analysis data | Additional LLM call and pipeline step |
| **In-memory FAISS index (ephemeral)** | Simple, no index staleness issues | Rebuilt per-request; not suitable for high-volume production use |
| **In-memory cache** | Zero-latency repeat lookups | Lost on restart; single-instance only |
| **sys.settrace for dynamic analysis** | Built-in Python; no sandbox dependencies | Cannot safely run truly malicious code; 5s timeout may miss long-running algorithms |
| **Judge Agent as last pipeline step** | Independent quality signal; does not influence generation | Adds latency; scores are informational only (no automatic regeneration of flagged questions) |
| **Temperature tuning per agent** | Optimises creativity vs. determinism per role | Manual tuning; different runs yield different results for creative agents |
| **gpt-4o-mini for cheap agents** | Significant cost reduction for high-volume stages (explanations, driver generation) | Slight quality reduction acceptable for these roles |

---

## 16. Limitations and Future Work

### Current Limitations

1. **Code safety**: The dynamic analysis sandbox uses a timeout but does not use OS-level process isolation (e.g., seccomp, Docker-in-Docker). Genuinely malicious code with file system access could cause harm in the current implementation.

2. **Language restriction**: Only Python is supported. The static analyser is built on Python's `ast` module; extending to other languages would require new analyser implementations.

3. **Cache durability**: In-memory cache is lost on restart. Production deployments would benefit from Redis or a persistent cache layer.

4. **Single-instance scaling**: The in-memory FAISS index and cache are not shared across multiple server instances.

5. **No automatic quality gating**: Flagged questions (low judge score) are displayed to students but not automatically regenerated.

6. **RAG index not persisted**: Lecture slides are re-embedded on every submission. A persistent index would improve response times for repeated use with the same slides.

### Potential Future Work

- **Adaptive question difficulty**: Track student performance over time and adjust question difficulty automatically.
- **Multi-language support**: Extend to Java, JavaScript using language-agnostic analysis (e.g., tree-sitter).
- **Persistent RAG index**: Maintain indexed lecture content per course module.
- **Automatic regeneration**: When Judge Agent flags a question, trigger a targeted regeneration pass.
- **Student analytics dashboard**: Aggregate student performance data to identify class-wide misconceptions.
- **Integration with LMS**: Deliver via Canvas/Moodle plugin rather than standalone web app.
- **Secure execution sandbox**: Use gVisor or Firecracker microVM for genuine code isolation.

---

## 17. Related Work

Key areas of related literature that should be covered in a full thesis:

1. **Automated question generation (AQG)** — Heilman & Smith (2010), Rus et al. (2010) — template-based and NLP approaches to question generation from text. QLC differs by targeting *code* rather than natural language.

2. **Program comprehension research** — Soloway & Ehrlich (1984), Wiedenbeck (1986), Schulte & Bennedsen (2006) — models of how programmers understand code; informs question taxonomy design.

3. **Formative assessment and feedback** — Black & Wiliam (1998) — foundational research on formative assessment effectiveness; establishes why immediate, specific feedback matters.

4. **LLMs for education** — Kasneci et al. (2023), Frieder et al. (2024) — recent surveys on LLM use in educational settings; covers opportunities and risks.

5. **LLMs for code generation and analysis** — Chen et al. (2021) Codex paper; Austin et al. (2021) — competence of LLMs on programming tasks; informs confidence in using GPT-4 for code-related question generation.

6. **Misconceptions in CS education** — Spohrer & Soloway (1986), Qian & Lehman (2017) — catalogues of documented programming misconceptions; informs the distractor design approach.

7. **Multi-agent LLM systems** — Chase (2022) LangChain, LangGraph documentation; Park et al. (2023) generative agents — background on multi-agent architectures for complex tasks.

8. **RAG systems** — Lewis et al. (2020) original RAG paper — theoretical basis for the lecture slide retrieval component.

---

## 18. Evaluation Methodology (Proposed)

A complete evaluation of the QLC system would address three questions:

### Q1: Technical Quality — Are the generated questions accurate and well-formed?
- Metric: Judge Agent scores (accuracy, clarity, pedagogical value, code specificity, difficulty calibration).
- Baseline: Human expert rating of the same questions.
- Comparison: Human–machine agreement on flagged questions.

### Q2: Pedagogical Effectiveness — Do students learn from answering QLC questions?
- Design: Randomised controlled trial — one group answers QLC questions after coding, control group receives only standard test feedback.
- Metric: Post-test conceptual understanding assessment.
- Secondary: Student-reported confidence, time on task.

### Q3: Coverage — Does the question set cover the Block Model levels appropriately?
- Metric: Distribution of questions across ATOM/BLOCK/RELATIONAL/MACRO levels.
- Analysis: Does the system consistently generate questions at all levels, or are some levels consistently under-represented?

---

## 19. Example End-to-End Flow

**Input Code**:
```python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
```

**Static Analysis Extracts**: `factorial` function, recursive (is_recursive=True), 1 parameter `n`, has conditional, 2 return statements.

**Dynamic Analysis Extracts**: `factorial` called 6 times (for n=5,4,3,2,1,0), return values 1,1,2,6,24,120, `result = 120`, max stack depth 6.

**Generated Questions (sample)**:
- [ATOM] "What is the value of `result` after line 6?" → Correct: 120, Distractor: 24 (off-by-one recursion level)
- [BLOCK] "How many times is `factorial` called in total when `factorial(5)` is executed?" → Correct: 6, Distractor: 5 (forgetting base case call)
- [RELATIONAL] "What is the relationship between the return value of `factorial(3)` and the computation on line 4 when `n=4`?" → Correct: "factorial(3) returns 6, which is then multiplied by 4 to give 24"
- [MACRO] "What would happen if the condition on line 2 were changed to `if n < 1`?" → Correct: "factorial(1) would enter infinite recursion and cause a RecursionError"

**Judge Evaluation (example)**:
- Mean accuracy: 4.8/5 | Mean pedagogical value: 4.3/5 | Mean overall: 4.4/5
- Questions flagged: 0

---

## 20. Repository Structure

```
FinalYearProject/
├── backend/
│   ├── analyzers/
│   │   ├── static_analyzer.py       # ast-based structure extraction
│   │   └── dynamic_analyzer.py      # sys.settrace execution tracing
│   ├── question_engine/
│   │   ├── state.py                 # QLCState TypedDict + make_initial_state()
│   │   ├── graph.py                 # LangGraph StateGraph + run_pipeline()
│   │   ├── tools.py                 # @tool wrappers for analyzers
│   │   ├── rag.py                   # FAISS-based lecture retrieval
│   │   ├── templates.py             # QuestionLevel, QuestionType enums
│   │   ├── answer_validator.py      # Semantic answer scoring
│   │   ├── generator.py             # Compatibility shim → run_pipeline()
│   │   └── agents/
│   │       ├── analyzer_agent.py
│   │       ├── question_agent.py
│   │       ├── answer_agent.py
│   │       ├── explanation_agent.py
│   │       └── judge_agent.py
│   ├── api/
│   │   ├── models.py                # Pydantic request/response schemas
│   │   ├── routes.py                # FastAPI endpoints
│   │   └── app.py
│   ├── database/
│   │   ├── models.py                # SQLAlchemy ORM
│   │   ├── crud.py
│   │   └── __init__.py
│   └── tests/
│       ├── test_answer_validator.py
│       ├── test_state.py
│       ├── test_tools.py
│       └── test_graph.py
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── CodeEditor.tsx
│       │   ├── QuestionPanel.tsx
│       │   ├── ResultsSummary.tsx
│       │   └── EvaluationPanel.tsx
│       ├── contexts/ThemeContext.tsx
│       └── lib/api.ts
├── docker-compose.yml
├── requirements.txt
└── CLAUDE.md
```

---

## Appendix A: Suggested Thesis Chapter Structure

1. **Introduction** — Problem motivation, research questions, scope
2. **Background and Related Work** — AQG, program comprehension, formative assessment, LLMs for education, multi-agent systems
3. **The Block Model and Question Design** — Deep dive into the cognitive taxonomy and its application
4. **System Design and Architecture** — High-level architecture, LangGraph pipeline rationale, QLCState design
5. **Code Analysis** — Static AST analysis, dynamic execution tracing, auto test driver
6. **Question Generation Pipeline** — Each agent in detail: prompt design, temperature, output schema, design decisions
7. **RAG Integration** — Lecture slide retrieval, ephemeral FAISS index, alignment with curriculum
8. **Frontend and User Experience** — React components, Monaco editor integration, question interface
9. **Implementation** — Technology stack, deployment, testing strategy
10. **Evaluation** — Question quality (judge scores), comparison with human ratings, case studies
11. **Discussion** — Limitations, lessons learned, comparison with prior approaches
12. **Conclusion and Future Work** — Summary of contributions, directions for future research

## Appendix B: Key References to Source

- Lehtinen, T., Santos, A. L., & Sorva, J. (2021). Let's Ask Students About Their Programs, Automatically. arXiv:2103.11138
- Black, P., & Wiliam, D. (1998). Assessment and Classroom Learning. Assessment in Education, 5(1), 7–74.
- Lewis, P., et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS 2020.
- Chen, M., et al. (2021). Evaluating Large Language Models Trained on Code (Codex). arXiv:2107.03374.
- Kasneci, E., et al. (2023). ChatGPT for Good? On Opportunities and Challenges of Large Language Models for Education. Learning and Individual Differences.
- Schulte, C., & Bennedsen, J. (2006). What do teachers teach in introductory programming? ICER '06.
- Spohrer, J. C., & Soloway, E. (1986). Novice mistakes: Are the folk wisdoms correct? CACM 29(7).
