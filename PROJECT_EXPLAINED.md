# Questions about Learners' Code (QLC) — Plain English Explanation

> This document explains the project in straightforward language. No coding background is assumed.

---

## 1. What is this project?

**QLC** stands for *Questions about Learners' Code*. It is an AI-powered web application that helps students learn programming better.

Here is the core idea:

> A student writes some Python code. Instead of just running it and seeing if it works, the system reads the code, understands what it does, and automatically creates a set of **quiz questions** about it. The student then answers those questions, which helps them check whether they really *understand* their own code — not just whether it produces the right output.

This is inspired by academic research (Lehtinen et al., 2021) which found that students often write code that works without truly understanding *why* it works. Asking targeted questions about their own code is a proven way to deepen understanding.

---

## 2. What does the user experience look like?

1. **Open the web app** in a browser.
2. **Paste or type Python code** into the editor on the left side of the screen.
3. **Click "Submit"** — the system processes the code behind the scenes.
4. **A set of multiple-choice questions appears** on the right side, each one specifically about the code the student submitted.
5. **The student picks an answer** for each question. The system immediately tells them if they were right or wrong, and explains *why*.
6. **An optional quality report** is also available, showing how good the generated questions are on several educational dimensions.

---

## 3. The two sides of the application

The application is split into two parts that talk to each other:

### The Frontend (what you see)
This is the visual interface running in your web browser. It is built with **React** — a popular technology for building interactive websites. It contains:
- A **code editor** (like a mini version of a coding tool) where the student types their Python code.
- A **question panel** that displays the generated multiple-choice questions one at a time.
- An **evaluation panel** that shows quality scores for the generated questions.
- A **results summary** showing statistics about the code (how many functions, loops, variables, etc.).

### The Backend (the engine)
This is the invisible part running on a server. It receives the student's code, runs the AI pipeline, and sends back the questions. It is built with **FastAPI** — a Python web framework — and uses **OpenAI's GPT models** (the same technology behind ChatGPT) to generate questions.

---

## 4. The AI pipeline — how questions are actually generated

This is the heart of the system. When a student submits code, it does not simply ask ChatGPT "make some questions about this code." Instead, it runs the code through a carefully designed **chain of specialised AI agents**, each doing one focused job. Think of it like an assembly line in a factory.

The pipeline uses a framework called **LangGraph**, which lets you define a series of steps (called "nodes") and connect them in a specific order, passing information from one step to the next.

Here is the full journey, step by step:

---

### Step 0 — Optional: Lecture Slide Lookup (RAG Retrieval)

**Only runs if a teacher has provided lecture slides.**

Before anything else, the system checks: *were any lecture slides uploaded?*

If yes, it performs what is called **RAG** (Retrieval-Augmented Generation). In plain terms:
- It breaks the lecture slides into small chunks of text.
- It converts each chunk into a mathematical representation (called an "embedding") that captures its meaning.
- It finds which chunks are most relevant to the student's code.
- It passes those relevant chunks to the later AI agents so questions can be aligned with what was actually taught in class.

If no lecture slides were provided, this step is skipped entirely.

---

### Step 1 — The Analyzer Agent: "What does this code do?"

**Model used: GPT-4o-mini (fast, cheap)**

Two types of analysis happen here:

#### Static Analysis — Reading the code without running it
The system reads the code like a very careful reader, using a technique called **AST (Abstract Syntax Tree)** analysis. Without executing a single line, it maps out:
- Every **function** defined (name, parameters, whether it calls itself recursively)
- Every **variable** (name, type, where it's used)
- Every **loop** (for/while, how deeply nested)
- Every **conditional** (if/else branches)
- **Classes**, decorators, imports, and more
- A rough measure of **complexity** for each function

#### Dynamic Analysis — Actually running the code
The system then **executes the code** in a controlled, sandboxed environment and watches what happens using Python's tracing system (`sys.settrace`). It records:
- What values variables hold when the code finishes
- Which functions were called, and in what order
- How many times each loop actually ran
- What was printed to the screen
- Whether the code ran successfully or crashed

#### Auto Test Driver
There is a clever sub-step here: if the student's code defines functions but never actually *calls* them (which is common when writing a library or utility), the system uses a small AI call to automatically write a few test calls. For example, if the student defines `def factorial(n):` but never calls it, the agent writes something like `result = factorial(5)` and appends it, so the dynamic analysis has something to trace.

**Output of this step:** a detailed structural and runtime "map" of the student's code.

---

### Step 2 — The Question Agent: "What should we ask?"

**Model used: GPT-4o (most capable)**

Armed with the analysis data from Step 1, this agent's sole job is to come up with **question ideas** — just the questions, no answers yet.

It uses a carefully designed system prompt that instructs it to think like a "computer science educator" and generate questions at four different cognitive levels, called the **Block Model**:

| Level | What it tests | Example |
|---|---|---|
| **ATOM** | Tiny details — a single variable or operator | "What is the value of `x` after line 3?" |
| **BLOCK** | A section of code — a loop or a function | "How many times does this loop execute?" |
| **RELATIONAL** | Connections between parts of the code | "How does the result of `helper()` affect `main()`?" |
| **MACRO** | The big picture — what does the whole program do? | "What is the overall purpose of this program?" |

Each question also has a **difficulty** (easy / medium / hard) and metadata like which line number or function name it refers to.

If lecture slide context was retrieved in Step 0, the agent is also told to align questions with the concepts taught in class.

**Output of this step:** a list of question texts with no answers.

---

### Step 3 — The Answer Agent: "What are the right and wrong answers?"

**Model used: GPT-4o**

This agent takes each question from Step 2 and generates:
- **1 correct answer** — verified against the analysis data (e.g., it checks the actual variable value from the dynamic analysis, not just guessing)
- **3 distractor answers** — wrong answers that are *plausible*, not obviously silly

The distractors are designed to target common student misconceptions. For example:
- Off-by-one errors (e.g., saying a loop runs 4 times when it runs 5)
- Wrong variable references (confusing `x` with `y`)
- Type confusion (saying a value is a string when it's an integer)
- Incorrect understanding of how recursion works

This is important because bad wrong answers (like "banana" for a numerical question) make quizzes trivially easy. Good distractors reveal genuine understanding gaps.

**Output of this step:** each question now has 4 answer choices (1 correct + 3 distractors).

---

### Step 4 — The Explanation Agent: "Why is each wrong answer wrong?"

**Model used: GPT-4o-mini**

For each of the 3 distractors in each question, this agent writes a short explanation of *why* it is wrong and what misconception it represents. This is shown to the student after they submit an answer, so they learn from their mistakes.

**Output of this step:** complete, fully-formed questions with all answer choices and explanations.

---

### Step 5 — The Judge Agent: "How good are these questions?"

**Model used: GPT-4o**

As the final step, an independent AI agent acts like a **quality reviewer**. It evaluates every generated question on 5 pedagogical dimensions and gives each one an integer score from 1 to 5:

| Dimension | What it measures |
|---|---|
| **Accuracy** *(weighted double)* | Is the correct answer actually correct? |
| **Clarity** | Is the question clearly and unambiguously worded? |
| **Pedagogical Value** *(weighted double)* | Does this question reveal meaningful understanding gaps? |
| **Code Specificity** | Can this only be answered by reading *this* code (vs. generic Python knowledge)? |
| **Difficulty Calibration** | Does the stated difficulty (easy/medium/hard) match how hard it actually is? |

A weighted overall score is computed. Any question scoring below 3.0, or with an accuracy score below 3, is **flagged** — meaning it is considered potentially problematic.

These evaluation results are stored and can be retrieved via the `/evaluate` endpoint. They are displayed in the app's Evaluation Panel.

---

## 5. Caching — not doing the same work twice

If a student submits the exact same code twice (with the same settings), the system recognises this and instantly returns the previously computed result from a **cache** (a short-term memory store), instead of running the full AI pipeline again. The cache lasts for 1 hour. This saves time and reduces API costs.

---

## 6. The database — remembering everything

Every submission is saved to a **SQLite database** (a simple file-based database). This stores:
- The student's original code
- All generated questions
- All answer choices
- When the submission happened and how long it took

This allows submissions to be retrieved later.

---

## 7. How the frontend and backend communicate

The frontend and backend talk to each other through a set of **API endpoints** — think of them as specific addresses you can send requests to, each with a defined purpose:

| Endpoint | What it does |
|---|---|
| `POST /api/submit-code` | Send code → get back questions |
| `POST /api/submit-answer` | Send a student's answer → get feedback |
| `GET /api/submission/{id}` | Retrieve a previous submission |
| `POST /api/evaluate/{id}` | Get quality scores for a submission |
| `GET /api/health` | Check if the system is running correctly |

---

## 8. Summary diagram

```
Student types code in browser
         │
         ▼
  [Frontend sends code to backend]
         │
         ▼
  Backend receives code
         │
         ├─ (if lecture slides provided) ──► Find relevant slide sections (RAG)
         │                                          │
         ▼                                          ▼
  Step 1: Analyzer Agent
    ├─ Read code structure (static analysis)
    ├─ Run code and watch it (dynamic analysis)
    └─ If needed: auto-generate test calls
         │
         ▼
  Step 2: Question Agent
    └─ Generate question ideas at 4 cognitive levels
         │
         ▼
  Step 3: Answer Agent
    └─ Add 1 correct answer + 3 plausible wrong answers
         │
         ▼
  Step 4: Explanation Agent
    └─ Write explanations for why each wrong answer is wrong
         │
         ▼
  Step 5: Judge Agent
    └─ Score every question on 5 quality dimensions
         │
         ▼
  Save to database
         │
         ▼
  Send questions back to frontend
         │
         ▼
Student sees questions, picks answers, gets feedback
```

---

## 9. Technologies used (in plain terms)

| Technology | Plain-English role |
|---|---|
| **Python** | The main programming language for the backend |
| **FastAPI** | The framework that handles incoming requests from the browser |
| **LangGraph** | The "assembly line" framework that connects the AI agents in sequence |
| **OpenAI GPT-4o / GPT-4o-mini** | The AI models that generate questions, answers, explanations, and scores |
| **FAISS** | A library that finds similar pieces of text (used for the lecture slide search) |
| **SQLite** | A simple file-based database that stores submissions and questions |
| **React** | The framework used to build the interactive browser interface |
| **Tailwind CSS** | A styling library that makes the interface look good |
| **Monaco Editor** | The code editor in the browser (the same editor used in VS Code) |
| **Docker** | A tool that packages the whole application so it can run anywhere |

---

## 10. The academic basis

This project is grounded in the research paper **"Let's Ask Students About Their Programs, Automatically"** (Lehtinen et al., 2021). The key insight from that research is that asking students targeted questions about their own code — not generic programming trivia — significantly improves understanding. The question levels (ATOM, BLOCK, RELATIONAL, MACRO) come directly from this paper's theoretical model of code comprehension.
