# Question Template System - Implementation Summary

## Overview

The Question Template System has been successfully implemented as part of the Questions about Learners' Code (QLC) system. This component bridges the gap between code analysis and question generation.

## What Was Implemented

### 1. Core Template Architecture (`backend/question_engine/templates.py`)

#### Data Structures
- **`QuestionLevel`** - Enum for Block Model levels (Atom, Block, Relational, Macro)
- **`QuestionType`** - Enum for answer formats (Multiple Choice, Fill-in-Blank, Numeric, etc.)
- **`AnswerType`** - Enum for how answers are determined (Static, Dynamic, Hybrid, OpenAI)
- **`QuestionAnswer`** - Data class for answer choices
- **`GeneratedQuestion`** - Complete question with metadata, answers, and context

#### Base Classes
- **`QuestionTemplate`** - Abstract base class for all templates
  - `is_applicable()` - Determines if template applies to given code
  - `generate_questions()` - Creates questions from analysis results

#### Template Registry
- **`TemplateRegistry`** - Central registry for template management
  - Singleton pattern via `get_registry()`
  - Template discovery and matching
  - Automatic registration of default templates

### 2. Initial Template Implementations

#### Template 1: Recursive Function Detection
- **ID:** `recursive_function_detection`
- **Type:** Multiple Choice
- **Level:** Block
- **Requirements:** 2+ function definitions
- **Analysis:** Static only
- **Question:** "Which functions are recursive?"
- **Answer:** Auto-generated from AST analysis

#### Template 2: Variable Value Tracing
- **ID:** `variable_value_tracing`
- **Type:** Fill-in-Blank
- **Level:** Atom
- **Requirements:** Successful execution with variables
- **Analysis:** Dynamic (execution required)
- **Question:** "What is the value of variable X on line Y?"
- **Answer:** Extracted from execution trace

#### Template 3: Loop Iteration Count
- **ID:** `loop_iteration_count`
- **Type:** Numeric
- **Level:** Block
- **Requirements:** Code has loops and executes
- **Analysis:** Dynamic (execution required)
- **Question:** "How many times does loop X iterate?"
- **Answer:** Counted during execution

### 3. Testing (`tests/test_question_templates.py`)

Comprehensive test suite with **25 unit tests** covering:
- Template applicability logic
- Question generation for each template
- Edge cases (no recursion, failed execution, etc.)
- Template registry functionality
- Integration with analyzers
- Question serialization

**Test Results:** ✅ All 25 tests passing

### 4. Demo Script (`demo_question_templates.py`)

Interactive demonstration showing:
- Template registry inspection
- Simple recursive function analysis
- Loop iteration analysis
- Complex program (Fibonacci) with multiple question types
- Questions grouped by comprehension level

## Key Features

### Template Matching System
The system intelligently determines which templates apply to student code:
```python
registry = get_registry()
applicable = registry.get_applicable_templates(static_analysis, dynamic_analysis)
```

### Multi-Level Analysis
Templates can require:
- **Static analysis only** - Fast, works on all code
- **Dynamic analysis only** - Requires execution
- **Hybrid** - Uses both for richer questions

### Extensibility
New templates can be easily added:
```python
class MyCustomTemplate(QuestionTemplate):
    def is_applicable(self, static_analysis, dynamic_analysis=None):
        # Custom logic

    def generate_questions(self, static_analysis, dynamic_analysis=None, source_code=None):
        # Question generation logic

registry.register(MyCustomTemplate())
```

### Rich Question Metadata
Every question includes:
- Template ID and name
- Question type and difficulty
- Comprehension level (Block Model)
- Context information (line numbers, variable names)
- Explanations for correct answers
- Answer choices (for multiple choice)

## File Structure

```
backend/question_engine/
├── __init__.py
└── templates.py              # Complete template system (600+ lines)

tests/
└── test_question_templates.py   # 25 comprehensive tests

demo_question_templates.py    # Interactive demo script
```

## Integration with Existing Components

The template system integrates seamlessly with:

1. **Static Analyzer** (`backend/analyzers/static_analyzer.py`)
   - Provides structural information about code
   - Function definitions, loops, variables, etc.

2. **Dynamic Analyzer** (`backend/analyzers/dynamic_analyzer.py`)
   - Provides runtime information
   - Variable values, iteration counts, execution flow

## Example Workflow

```python
from backend.analyzers.static_analyzer import StaticAnalyzer
from backend.analyzers.dynamic_analyzer import DynamicAnalyzer
from backend.question_engine.templates import get_registry

# Student submits code
code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""

# Analyze the code
static_analysis = StaticAnalyzer().analyze(code)
dynamic_analysis = DynamicAnalyzer().analyze(code)

# Find applicable templates
registry = get_registry()
templates = registry.get_applicable_templates(static_analysis, dynamic_analysis)

# Generate questions
questions = []
for template in templates:
    questions.extend(
        template.generate_questions(static_analysis, dynamic_analysis, code)
    )

# Present questions to student
for q in questions:
    print(q.question_text)
    print(f"Answer: {q.correct_answer}")
```

## Design Decisions

### 1. Template Pattern
Chose the template pattern to allow easy addition of new question types without modifying core logic.

### 2. Separation of Concerns
Templates only handle question generation. Analysis is handled by separate components.

### 3. Declarative Requirements
Templates declare what they need (`is_applicable()`), making it easy to understand prerequisites.

### 4. Rich Metadata
Questions carry comprehensive context to support future features (hints, adaptive difficulty, etc.).

### 5. Type Safety
Used enums and data classes for type safety and IDE support.

## Limitations & Future Work

### Current Limitations
1. Limited to 3 initial templates
2. No relational or macro-level questions yet
3. No OpenAI integration for open-ended answers
4. Function variable tracking could filter out function definitions better

### Planned Enhancements
1. Additional templates:
   - Call stack depth questions (Relational)
   - Algorithm complexity questions (Macro)
   - Variable scope questions (Relational)
   - Error detection questions (Block)

2. Smart question selection:
   - Avoid duplicate/similar questions
   - Prioritize by difficulty
   - Limit total questions per submission

3. OpenAI-enhanced questions:
   - Natural language explanations
   - Open-ended "why" questions
   - Automated grading of free-text answers

## Testing Summary

**Total Tests:** 60 (25 new + 35 existing)
**Status:** ✅ All passing
**Coverage:**
- Template applicability logic ✓
- Question generation ✓
- Registry management ✓
- Integration with analyzers ✓
- Edge cases ✓

## Conclusion

The Question Template System provides a robust, extensible foundation for generating comprehension questions about student code. It successfully combines static and dynamic analysis to create contextual questions at multiple comprehension levels.

The system is ready for integration with the next components:
- Question Generator (orchestration layer)
- REST API backend
- Frontend UI
- Database persistence

---

**Implementation Date:** 2025-10-21
**Lines of Code:** ~600 (templates.py) + ~400 (tests)
**Test Coverage:** 25 unit tests, all passing
