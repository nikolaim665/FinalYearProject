# Questions about Learners' Code (QLC) System

[![CI](https://github.com/nikolaim665/FinalYearProject/actions/workflows/ci.yml/badge.svg)](https://github.com/nikolaim665/FinalYearProject/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Final Year Project implementing an automated system for generating and presenting questions about student-written code to enhance program comprehension and assessment.

## Project Overview

This project implements the concept of **Questions about Learners' Code (QLCs)** - automatically generated questions about student programs that probe their understanding of their own code. Based on the research paper "Let's Ask Students About Their Programs, Automatically" by Lehtinen et al. (2021).

### Core Concept

Students often produce code that works but don't fully comprehend it. This system:

- Analyzes student-submitted Python code
- Generates targeted questions about their code
- Presents questions in an interactive web interface
- Provides immediate feedback on answers
- Assesses program comprehension beyond functional correctness

## Architecture

```
┌─────────────────┐
│  Student Code   │
└────────┬────────┘
         │
    ┌────▼─────┐
    │ Analysis │
    │  Engine  │
    └────┬─────┘
         │
    ┌────▼──────────────────┐
    │                       │
┌───▼────────┐   ┌─────────▼────────┐
│   Static   │   │     Dynamic      │
│  Analyzer  │   │  Analyzer (Run)  │
└───┬────────┘   └─────────┬────────┘
    │                      │
    └──────────┬───────────┘
               │
        ┌──────▼──────┐
        │  Template   │
        │  Database   │
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │  Question   │
        │   Engine    │
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │    QLCs     │
        └─────────────┘
```

## Technology Stack

### Backend

- **Python 3.14**
- **Flask/FastAPI**: REST API for code submission and question generation
- **AST (Abstract Syntax Tree)**: Static code analysis
- **trace/sys.settrace()**: Dynamic execution analysis
- **OpenAI API**: Enhanced question generation and open-ended answer assessment

### Frontend

- **React**: UI framework
- **Monaco Editor**: Code editor (VS Code's editor)
- **Tailwind CSS**: Styling
- **Axios**: HTTP client

### Database

- **SQLite** (development) / **PostgreSQL** (production)
- Store submissions, questions, and student responses

## Question Types (Block Model)

### Atom Level (Language Elements)

- "Which of the following are variable names in your function?"
- "What is assigned to variable `x` on line 5?"

### Block Level (Code Sections)

- "Enter the line number where this loop ends"
- "How many iterations does the loop perform?"

### Relational Level (Connections)

- "How deep does the call stack grow?"
- "Which line number declares the variable used on line X?"

### Macro Level (Whole Program)

- "Explain the overall purpose of your program"
- "What is the time complexity of your solution?"

## Initial Template Examples

1. **Recursive Function Detection**
   - Requirement: Program contains function definitions
   - Question: "Which of the following are recursive functions?"
   - Answer: Auto-generated from static analysis

2. **Variable Tracing**
   - Requirement: Program executes successfully
   - Question: "What is the value of variable `{var}` on line {n} when executing `{function}({args})`?"
   - Answer: Auto-generated from dynamic analysis

3. **Loop Iteration Count**
   - Requirement: Program contains loops
   - Question: "How many iterations does the loop starting on line {n} perform?"
   - Answer: Auto-generated from dynamic analysis

## Current Implementation Status

### ✅ Completed Components

1. **Static Analyzer** (`backend/analyzers/static_analyzer.py`)
   - AST-based code analysis
   - Extracts functions, variables, loops, conditionals
   - Detects recursive functions
   - Fully tested

2. **Dynamic Analyzer** (`backend/analyzers/dynamic_analyzer.py`)
   - Execution tracing using `sys.settrace()`
   - Captures variable values at runtime
   - Counts loop iterations
   - Tracks function calls and stack depth
   - Fully tested

3. **Question Template System** (`backend/question_engine/templates.py`)
   - Template registry and matching system
   - 3 initial templates implemented:
     - Recursive function detection (BLOCK level)
     - Variable value tracing (ATOM level)
     - Loop iteration counting (BLOCK level)
   - Support for multiple question types and difficulty levels
   - Fully tested with 25 unit tests

4. **Question Generator** (`backend/question_engine/generator.py`)
   - Complete end-to-end pipeline orchestration
   - Combines static and dynamic analysis
   - Flexible configuration system
   - Multiple selection strategies (Diverse, Focused, All, Adaptive)
   - Advanced filtering and deduplication
   - JSON serialization for API integration
   - Robust error handling
   - Fully tested with 26 unit tests

### 🎯 Core System Complete

The complete question generation pipeline is now operational:

- ✅ Code Analysis (Static + Dynamic)
- ✅ Question Template System
- ✅ Question Generation & Selection
- ✅ 86 passing tests
- ✅ Complete demos available

### 🚧 Next Steps

1. **Flask/FastAPI Backend** - REST API for code submission
2. **Database Models** - Store submissions, questions, and answers
3. **React Frontend** - Interactive UI with code editor
4. **Answer Assessment** - Grade student responses
5. **OpenAI Integration** - Enhanced question generation and grading

## Getting Started

### Prerequisites

```bash
python --version  # Python 3.14+
node --version    # Node 16+ (for frontend, when implemented)
```

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd FinalYearProject
```

2. Set up Python virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install Python dependencies:

```bash
pip install -r requirements.txt
```

4. (Optional) Install frontend dependencies when frontend is implemented:

```bash
cd frontend
npm install
```

### Running Demos

Try out the implemented components:

```bash
# Demo: Static Analyzer
python demo_static_analyzer.py

# Demo: Dynamic Analyzer
python demo_dynamic_analyzer.py

# Demo: Question Template System
python demo_question_templates.py

# Demo: Complete Pipeline (Question Generator)
python demo_question_generator.py
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test files
python -m pytest tests/test_static_analyzer.py -v
python -m pytest tests/test_dynamic_analyzer.py -v
python -m pytest tests/test_question_templates.py -v
```

### Environment Setup (for future OpenAI integration)

5. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your OpenAI API key and other settings
```

### Running the Application

1. Start the backend:

```bash
python app.py
# Backend runs on http://localhost:5000
```

2. Start the frontend (in a new terminal):

```bash
cd frontend
npm start
# Frontend runs on http://localhost:3000
```

3. Open <http://localhost:3000> in your browser

## Configuration

See `config/settings.py` for:

- Question template settings
- Analysis engine configuration
- OpenAI API settings
- Teacher-specific configurations

## Project Structure

```
FinalYearProject/
├── backend/
│   ├── analyzers/
│   │   ├── static_analyzer.py
│   │   └── dynamic_analyzer.py
│   ├── question_engine/
│   │   ├── templates.py
│   │   ├── generator.py
│   │   └── assessor.py
│   ├── api/
│   │   ├── routes.py
│   │   └── models.py
│   ├── openai_integration/
│   │   ├── enhancer.py
│   │   └── grader.py
│   └── app.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CodeEditor.jsx
│   │   │   ├── QuestionPanel.jsx
│   │   │   └── FeedbackDisplay.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   └── App.jsx
│   └── package.json
├── tests/
│   ├── test_static_analyzer.py
│   ├── test_dynamic_analyzer.py
│   └── test_question_engine.py
├── docs/
│   ├── architecture.md
│   ├── api-reference.md
│   └── user-guide.md
├── requirements.txt
├── OriginalPaper.pdf
└── README.md
```

## References

Lehtinen, T., Santos, A. L., & Sorva, J. (2021). Let's Ask Students About Their Programs, Automatically. arXiv:2103.11138 [cs.CY]

## Contributors

- Nicolas Moschenross

## Acknowledgments

Based on research by Teemu Lehtinen, André L. Santos, and Juha Sorva at Aalto University and ISCTE-IUL.
