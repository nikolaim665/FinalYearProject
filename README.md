# Questions about Learners' Code (QLC) System

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

## Implementation Roadmap

### Phase 1: Core Analysis Engine (Weeks 1-4)

#### Step 1.1: Static Code Analyzer

- [ ] Set up Python AST parser
- [ ] Extract basic facts:
  - [ ] Variable declarations and names
  - [ ] Function definitions and signatures
  - [ ] Loop structures (for, while) with line numbers
  - [ ] Conditional statements (if/else)
  - [ ] Identify recursive functions
- [ ] Create data structure for static facts
- [ ] Unit tests for analyzer

#### Step 1.2: Dynamic Code Analyzer

- [ ] Implement safe code execution sandbox
- [ ] Execute with test cases
- [ ] Collect runtime facts:
  - [ ] Variable values at specific execution points
  - [ ] Call stack depth tracking
  - [ ] Loop iteration counts
  - [ ] Execution flow sequence
- [ ] Handle errors gracefully
- [ ] Unit tests for execution engine

#### Step 1.3: Question Template System

- [ ] Design template data structure
- [ ] Implement Block Model levels (Atom, Block, Relational, Macro)
- [ ] Create initial template set:
  - [ ] 5 atom-level templates (simple facts)
  - [ ] 5 block-level templates (code sections)
  - [ ] 3 relational templates (connections)
  - [ ] 2 macro templates (whole program)
- [ ] Template matching algorithm
- [ ] Answer generation logic

#### Step 1.4: Question Engine

- [ ] Template selection algorithm
- [ ] Placeholder replacement system
- [ ] Question instantiation
- [ ] Answer verification system
- [ ] Randomization and variety control

### Phase 2: Web Interface (Weeks 5-6)

#### Step 2.1: Backend API

- [ ] Set up Flask/FastAPI project structure
- [ ] Create endpoints:
  - [ ] `POST /api/submit`: Submit code
  - [ ] `POST /api/analyze`: Trigger analysis
  - [ ] `GET /api/questions/:submission_id`: Get questions
  - [ ] `POST /api/answer`: Submit answer
  - [ ] `GET /api/feedback/:answer_id`: Get feedback
- [ ] Integrate analysis engine
- [ ] Database models and migrations
- [ ] API documentation

#### Step 2.2: Frontend - Code Input Panel

- [ ] Initialize React app
- [ ] Set up routing
- [ ] Implement Monaco Editor
- [ ] Code submission form
- [ ] Syntax highlighting for Python
- [ ] Loading states and error handling

#### Step 2.3: Frontend - QLC Display Panel

- [ ] Split-panel layout
- [ ] Question rendering component
- [ ] Answer input forms:
  - [ ] Multiple choice
  - [ ] Single value (text/number)
  - [ ] Open-ended text
- [ ] Submit answer functionality
- [ ] Feedback display
- [ ] Progress tracking

#### Step 2.4: Integration

- [ ] Connect frontend to backend API
- [ ] State management (Context API/Redux)
- [ ] Real-time updates
- [ ] Session management
- [ ] Error handling and user feedback

### Phase 3: OpenAI Integration (Weeks 7-8)

#### Step 3.1: Question Enhancement

- [ ] Set up OpenAI API client
- [ ] Implement question rephrasing
- [ ] Natural language generation for questions
- [ ] Context-aware question formulation
- [ ] A/B testing template vs AI questions

#### Step 3.2: Open-Ended Answer Assessment

- [ ] Prompt engineering for answer grading
- [ ] Semantic similarity comparison
- [ ] Partial credit assignment
- [ ] Feedback generation
- [ ] Confidence scoring

#### Step 3.3: Advanced Question Generation

- [ ] "Explain the purpose" questions
- [ ] "What-if" scenario questions
- [ ] Design decision questions
- [ ] Code comparison questions

### Phase 4: Testing & Refinement (Weeks 9-10)

#### Step 4.1: Unit & Integration Testing

- [ ] Backend test coverage >80%
- [ ] Frontend component tests
- [ ] End-to-end tests with Cypress/Playwright
- [ ] API contract tests

#### Step 4.2: User Testing

- [ ] Pilot study with 10-15 students
- [ ] Collect feedback on:
  - [ ] Question clarity
  - [ ] Interface usability
  - [ ] Question difficulty
  - [ ] Learning value
- [ ] Iterate based on feedback

#### Step 4.3: Documentation

- [ ] API documentation
- [ ] User guide
- [ ] Teacher configuration guide
- [ ] Template creation guide
- [ ] Deployment guide

### Phase 5: Deployment & Evaluation (Weeks 11-12)

#### Step 5.1: Deployment

- [ ] Set up production environment
- [ ] Configure CI/CD pipeline
- [ ] Deploy backend (Heroku/AWS/GCP)
- [ ] Deploy frontend (Vercel/Netlify)
- [ ] Set up monitoring and logging

#### Step 5.2: Evaluation Study

- [ ] Define research questions
- [ ] Recruit participants
- [ ] Collect data:
  - [ ] Student responses to QLCs
  - [ ] Comprehension scores
  - [ ] User experience surveys
  - [ ] Learning outcomes
- [ ] Analyze results
- [ ] Write final report

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

## Getting Started

### Prerequisites

```bash
python --version  # Python 3.14+
node --version    # Node 16+
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

4. Install frontend dependencies:

```bash
cd frontend
npm install
```

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
