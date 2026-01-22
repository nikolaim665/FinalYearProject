# Questions about Learners' Code (QLC) System

[![CI](https://github.com/nikolaim665/FinalYearProject/actions/workflows/ci.yml/badge.svg)](https://github.com/nikolaim665/FinalYearProject/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

An automated system for generating comprehension questions about student-written Python code. Uses AI (OpenAI GPT-5.2) combined with static and dynamic code analysis to create pedagogically valuable questions.

Based on the research paper "Let's Ask Students About Their Programs, Automatically" by Lehtinen et al. (2021).

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 16+
- OpenAI API key

### Installation

```bash
# Clone and setup
git clone <repository-url>
cd FinalYearProject

# Python setup
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY="your-key-here"

# Frontend setup
cd frontend && npm install && cd ..
```

### Running

```bash
# Terminal 1: Start backend
python run_api.py
# API: http://localhost:8000
# Docs: http://localhost:8000/docs

# Terminal 2: Start frontend
cd frontend && npm run dev
# App: http://localhost:3000
```

---

## Architecture

```
Student Code → Static Analyzer (AST) ──┐
                                       ├→ OpenAI GPT-5.2 → Questions
             → Dynamic Analyzer (exec) ─┘
```

### Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Static Analyzer | `backend/analyzers/static_analyzer.py` | AST-based code structure extraction |
| Dynamic Analyzer | `backend/analyzers/dynamic_analyzer.py` | Runtime tracing via `sys.settrace()` |
| AI Generator | `backend/question_engine/ai_generator.py` | GPT-5.2 question generation |
| REST API | `backend/api/` | FastAPI endpoints |
| Database | `backend/database/` | SQLAlchemy with SQLite/PostgreSQL |
| Frontend | `frontend/` | React + Vite + Monaco Editor |

---

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/submit-code` | Submit code, get AI-generated questions |
| POST | `/api/submit-answer` | Submit answer, get feedback |
| GET | `/api/submission/{id}` | Retrieve submission |
| GET | `/api/submissions` | List all submissions |
| GET | `/api/templates` | List generation info |

### Submit Code Example

```bash
curl -X POST "http://localhost:8000/api/submit-code" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n\nresult = factorial(5)",
    "max_questions": 5
  }'
```

### Response

```json
{
  "submission_id": "sub_abc123",
  "questions": [
    {
      "id": "q_xyz789",
      "question_text": "Which functions are recursive?",
      "question_type": "multiple_choice",
      "question_level": "block",
      "correct_answer": "factorial",
      "answer_choices": [...],
      "difficulty": "medium"
    }
  ],
  "metadata": {
    "total_generated": 5,
    "execution_successful": true,
    "execution_time_ms": 1250.5
  }
}
```

---

## Question Types

### Levels (Block Model)

- **ATOM**: Language elements (variables, values, types)
- **BLOCK**: Code sections (loops, functions, conditionals)
- **RELATIONAL**: Connections between parts (call relationships)
- **MACRO**: Whole program understanding (purpose, complexity)

### Formats

- Multiple choice
- Fill-in-blank
- Numeric
- True/False
- Short answer

---

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your-openai-key

# Optional
DATABASE_URL=sqlite+aiosqlite:///./qlc_database.db  # or PostgreSQL
```

### Generation Options

```json
{
  "code": "...",
  "max_questions": 10,
  "strategy": "diverse",
  "allowed_levels": ["atom", "block"],
  "allowed_types": ["multiple_choice", "numeric"],
  "allowed_difficulties": ["easy", "medium"]
}
```

---

## Database

### Schema

```
code_submissions (id, submission_id, code, analysis_summary, status, timestamps)
    └── questions (id, question_id, template_id, question_text, correct_answer, ...)
        └── answers (id, answer_id, student_answer, is_correct, score, feedback)
```

### Migrations

```bash
alembic upgrade head      # Apply migrations
alembic downgrade -1      # Rollback
alembic revision --autogenerate -m "description"  # New migration
```

---

## Development

### Running Tests

```bash
# All tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=backend --cov-report=html

# Specific component
python -m pytest tests/test_static_analyzer.py -v
```

### CI/CD

GitHub Actions runs on every push:
- Tests on Python 3.10, 3.11, 3.12
- Code coverage tracking
- Code quality checks (black, isort, flake8)
- Security scanning (safety, bandit)

### Project Structure

```
FinalYearProject/
├── backend/
│   ├── analyzers/           # Static & dynamic analysis
│   ├── question_engine/     # AI-powered generation
│   ├── api/                 # FastAPI routes & models
│   └── database/            # SQLAlchemy ORM
├── frontend/                # React + Vite
├── tests/                   # Pytest suite
├── alembic/                 # DB migrations
└── requirements.txt
```

---

## Deployment

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ backend/
COPY run_api.py .
EXPOSE 8000
CMD ["python", "run_api.py"]
```

### Production

```bash
# Backend with Gunicorn
pip install gunicorn uvicorn[standard]
gunicorn backend.api.app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Frontend build
cd frontend && npm run build
# Deploy dist/ to static hosting
```

---

## Security Notes

- Code execution has 5-second timeout
- Use containers/VMs for sandboxing in production
- Restrict CORS origins in production
- Add authentication for multi-user deployments
- Rate limit API endpoints

---

## References

Lehtinen, T., Santos, A. L., & Sorva, J. (2021). Let's Ask Students About Their Programs, Automatically. arXiv:2103.11138

## Author

Nicolas Moschenross
