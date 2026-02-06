# CLAUDE.md

## Project Overview

**Questions about Learners' Code (QLC)** - An AI-powered system that generates comprehension questions about student-written Python code, based on "Let's Ask Students About Their Programs, Automatically" (Lehtinen et al., 2021).

## Tech Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy (async), Alembic, OpenAI GPT-5.2
- **Frontend**: React 19, Vite, Tailwind CSS, Monaco Editor, Lucide icons
- **Database**: SQLite (aiosqlite) / PostgreSQL
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
    routes_db.py          # FastAPI REST endpoints
  database/
    models.py             # SQLAlchemy ORM models
    crud.py               # Database operations
    __init__.py           # DB session/engine setup
frontend/
  src/
    components/
      QuestionPanel.jsx   # Question display, answer input, detailed explanations
      CodeEditor.jsx      # Monaco-based Python editor
      ResultsSummary.jsx   # Analysis results display
    pages/
      CodingPage.jsx      # Main coding interface
      ResultsPage.jsx     # Results review
    services/
      api.js              # Axios HTTP client
tests/                    # pytest test suite
alembic/                  # Database migrations
```

## Architecture: Two-LLM Pipeline

1. **Static Analyzer** - Parses code via AST (functions, variables, loops, classes, complexity)
2. **Dynamic Analyzer** - Executes code with `sys.settrace()` (runtime values, loop counts, call graph)
3. **LLM #1 (AI Generator)** - Generates questions at 4 levels (ATOM/BLOCK/RELATIONAL/MACRO) with correct answers
4. **LLM #2 (Answer Explainer)** - Verifies each answer against code+analysis, explains why correct answer is correct, why wrong answers are wrong, provides code references and learning tips

The explainer receives full context (source code + static analysis + dynamic analysis) to ground its explanations in actual code behavior.

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

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
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
- `DATABASE_URL` - Optional, defaults to `sqlite+aiosqlite:///./qlc_database.db`

## Configuration Flags

In `GenerationConfig` (ai_generator.py):
- `enable_explainer: bool = True` - Toggle the second LLM (answer explainer)
- `explainer_model: str` - Model for the explainer (defaults to same as generator)
- `explainer_temperature: float = 0.3` - Lower temp for factual explanations
- `enable_caching: bool = True` - Cache identical code submissions
- `max_questions: int = 10` - Max questions per submission

## Question Levels (Block Model)

- **ATOM** - Language elements (variable values, types)
- **BLOCK** - Code sections (loop counts, function returns)
- **RELATIONAL** - Connections between parts (how functions interact)
- **MACRO** - Whole program understanding (purpose, overall behavior)

## Database Migrations

Latest migration chain:
1. `ce8f50213406` - Initial schema (submissions, questions, answers)
2. `35757c730081` - Add alternative_answers column
3. `a1b2c3d4e5f6` - Add answer_explanation column (rich LLM explanations)

## Code Style

- Backend: Python, no strict formatter enforced but CI checks black/isort/flake8
- Frontend: JSX, Tailwind utility classes, functional components with hooks
- No TypeScript in frontend (plain JSX)
- Pydantic v2 for API validation, SQLAlchemy 2.0 mapped_column style for ORM
