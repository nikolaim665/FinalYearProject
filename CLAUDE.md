# CLAUDE.md

## Project Overview

**Questions about Learners' Code (QLC)** - An AI-powered system that generates comprehension questions about student-written Python code, based on "Let's Ask Students About Their Programs, Automatically" (Lehtinen et al., 2021).

## Tech Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy 2.0 (sync), OpenAI o4-mini (generator) / gpt-4.1-mini (test driver) / gpt-5.2 (explainer)
- **Frontend**: React 19, Vite, Tailwind CSS, Monaco Editor, Lucide icons
- **Database**: SQLite via SQLAlchemy (persisted in Docker via named volume `qlc_data` at `/data/qlc.db`)
- **Testing**: pytest (async), GitHub Actions CI

## Project Structure

```
backend/
  analyzers/
    static_analyzer.py    # AST-based code structure analysis
    dynamic_analyzer.py   # Runtime tracing via sys.settrace()
  question_engine/
    ai_generator.py       # LLM #1: generates questions from analysis data
    answer_explainer.py   # LLM #2: verifies answers, generates rich explanations
    answer_validator.py   # Semantic answer validation (synonyms, partial match)
  api/
    models.py             # Pydantic request/response schemas
    routes.py             # FastAPI REST endpoints
  database/
    models.py             # SQLAlchemy ORM models (Submission, Question, AnswerChoice)
    crud.py               # save_submission() — persists full question+choice tree
    __init__.py           # engine, SessionLocal, get_db(), init_db()
frontend/
  src/
    components/
      QuestionPanel.tsx   # Question display, answer input, detailed explanations
      CodeEditor.tsx      # Monaco-based Python editor
      ResultsSummary.tsx  # Analysis results display
      EvaluationPanel.tsx # LLM judge evaluation display
    contexts/
      ThemeContext.tsx    # Dark/light mode context
    hooks/               # Custom React hooks
tests/                    # pytest test suite
```

## Architecture: Two-LLM Pipeline

1. **Static Analyzer** - Parses code via AST (functions, variables, loops, classes, complexity)
2. **Test Driver Generator** - If the code has no module-level calls, a cheap `gpt-4.1-mini` call generates a try/except-wrapped driver snippet (e.g. `_qlc_r1 = factorial(5)`) that is appended before dynamic analysis so `sys.settrace` has real calls to trace. The original source is unchanged for question generation.
3. **Dynamic Analyzer** - Executes the (possibly augmented) code with `sys.settrace()` (runtime values, loop counts, call graph)
4. **LLM #1 (AI Generator, `o4-mini`)** - Generates questions at 4 levels (ATOM/BLOCK/RELATIONAL/MACRO) with correct answers. Uses Structured Outputs (strict JSON Schema) to guarantee response shape and eliminate parse failures.
5. **LLM #2 (Answer Explainer, `gpt-5.2`)** - Verifies each answer against code+analysis, explains why the correct answer is correct, why wrong answers are wrong, provides code references and learning tips. Receives pre-optimized (trimmed) analysis data. Explanation batches run in parallel via `ThreadPoolExecutor`.

Both LLMs use OpenAI Structured Outputs (`response_format: json_schema, strict: true`) — no more silent question drops from JSON parse errors.

## Key Commands

```bash
# Backend
cd backend && uvicorn api.main:app --reload --port 8000
# or: python run_api.py

# Frontend
cd frontend && npm run dev    # Dev server on port 3000
cd frontend && npm run build  # Production build

# Tests
pytest tests/

# Docker (production)
docker compose up --build

# Database — interactive SQLite shell inside running container
docker exec -it qlc-backend sqlite3 /data/qlc.db

# Database — copy DB file out for GUI tools (DB Browser, DBeaver, TablePlus)
docker cp qlc-backend:/data/qlc.db ./qlc.db
```

## API Endpoints

- `POST /api/submit-code` - Submit code, run analysis, generate questions with explanations
- `POST /api/submit-answer` - Submit answer, get feedback (uses rich explanations for wrong answers)
- `GET /api/submission/{id}` - Retrieve submission with questions and explanations
- `GET /api/submissions` - List all submissions (paginated)
- `GET /api/health` - Health check
- `GET /api/templates` - Generation system info

## Environment Variables

- `OPENAI_API_KEY` - Required for question generation and answer explanation
- `DATABASE_URL` - Optional. In Docker defaults to `sqlite:////data/qlc.db`; locally falls back to `sqlite:///<project-root>/qlc.db`

## Configuration Flags

In `GenerationConfig` (ai_generator.py):
- `model: str = "o4-mini"` - Model for question generation
- `driver_model: str = "gpt-4.1-mini"` - Cheap model used for auto test-driver generation
- `enable_auto_driver: bool = True` - Auto-generate test inputs when code has no module-level calls
- `enable_explainer: bool = True` - Toggle the second LLM (answer explainer)
- `explainer_model: str = "gpt-5.2"` - Model for the explainer
- `explainer_temperature: float = 0.3` - Lower temp for factual explanations
- `enable_caching: bool = True` - Cache identical code submissions (key includes levels + types filters)
- `max_questions: int = 10` - Max questions per submission

## Question Types

- **multiple_choice** - 4 options, one correct (most common)
- **true_false** - True or False statement about the code
- **numeric** - Student provides a number (e.g. loop count, return value)

> `fill_in_blank` and `short_answer` (open-ended) have been removed. The LLM
> prompt, enums, and frontend all enforce only the three types above.

## Question Levels (Block Model)

- **ATOM** - Language elements (variable values, types)
- **BLOCK** - Code sections (loop counts, function returns)
- **RELATIONAL** - Connections between parts (how functions interact)
- **MACRO** - Whole program understanding (purpose, overall behavior)

## Database Schema

Three tables, created automatically via `Base.metadata.create_all()` on startup (no migrations needed):

| Table | Key columns |
|---|---|
| `submissions` | `id`, `code`, `created_at`, `execution_time_ms`, `total_questions`, `errors` |
| `questions` | `id`, `submission_id` (FK), `question_text`, `question_type`, `question_level`, `correct_answer`, `difficulty`, `explanation` |
| `answer_choices` | `id`, `question_id` (FK), `text`, `is_correct`, `explanation` |

Each question has one `answer_choices` row with `is_correct=1` and up to three with `is_correct=0` (distractors).
See `docs/database-queries.md` for query examples.

## Code Style

- Backend: Python, no strict formatter enforced but CI checks black/isort/flake8
- Frontend: TypeScript (TSX), Tailwind utility classes, functional components with hooks
- Pydantic v2 for API validation, SQLAlchemy 2.0 `DeclarativeBase` style for ORM
- DB sessions injected via `Depends(get_db)` in route functions; never use `SessionLocal` directly in routes
