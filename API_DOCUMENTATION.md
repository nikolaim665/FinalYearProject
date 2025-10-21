

# QLC REST API Documentation

## Overview

The **QLC (Questions about Learners' Code) REST API** provides automated question generation for Python code submissions. It analyzes student code and generates contextual questions to assess program comprehension.

## Base URL

```
http://localhost:8000
```

## Quick Start

### 1. Start the API Server

```bash
python run_api.py
```

The API will be available at `http://localhost:8000`

### 2. Access Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. Submit Code and Get Questions

```bash
curl -X POST "http://localhost:8000/api/submit-code" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n\nresult = factorial(5)",
    "max_questions": 5
  }'
```

## API Endpoints

### System Endpoints

#### GET `/` - Root
Returns API information and available endpoints.

**Response:**
```json
{
  "message": "QLC API - Questions about Learners' Code",
  "version": "1.0.0",
  "docs": "/docs",
  "endpoints": {
    "submit_code": "POST /api/submit-code",
    "submit_answer": "POST /api/submit-answer",
    "get_submission": "GET /api/submission/{id}",
    "list_templates": "GET /api/templates"
  }
}
```

#### GET `/api/health` - Health Check
Check API health and component status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "static_analyzer": "ok",
    "dynamic_analyzer": "ok",
    "template_system": "ok",
    "templates_loaded": "3"
  }
}
```

### Question Generation

#### POST `/api/submit-code` - Submit Code for Analysis
Submit Python code and receive generated questions.

**Request Body:**
```json
{
  "code": "string (required, 1-50000 chars)",
  "test_inputs": {
    "key": "value"  // optional, for dynamic analysis
  },
  "max_questions": 10,  // optional, 1-50, default: 10
  "strategy": "diverse",  // optional: "all", "diverse", "focused", "adaptive"
  "allowed_levels": ["atom", "block"],  // optional filter
  "allowed_types": ["multiple_choice", "numeric"],  // optional filter
  "allowed_difficulties": ["easy", "medium"]  // optional filter
}
```

**Response (201 Created):**
```json
{
  "submission_id": "sub_abc123def456",
  "questions": [
    {
      "id": "q_xyz789",
      "template_id": "recursive_function_detection",
      "question_text": "Which functions are recursive?",
      "question_type": "multiple_choice",
      "question_level": "block",
      "answer_type": "static",
      "correct_answer": "factorial",
      "answer_choices": [
        {
          "text": "factorial",
          "is_correct": true,
          "explanation": "Calls itself"
        },
        {
          "text": "helper",
          "is_correct": false
        }
      ],
      "context": {
        "total_functions": 2,
        "recursive_count": 1
      },
      "explanation": "factorial calls itself on line 4",
      "difficulty": "medium"
    }
  ],
  "metadata": {
    "total_generated": 5,
    "total_filtered": 0,
    "total_returned": 5,
    "applicable_templates": 3,
    "execution_successful": true,
    "execution_time_ms": 12.5
  },
  "analysis_summary": {
    "total_functions": 2,
    "total_variables": 1,
    "total_loops": 0,
    "has_recursion": true,
    "execution_successful": true,
    "max_stack_depth": 6
  },
  "errors": [],
  "warnings": []
}
```

**Errors:**
- `400 Bad Request` - Syntax error in code
- `422 Unprocessable Entity` - Validation error (empty code, invalid parameters)
- `500 Internal Server Error` - Generation failed

### Answer Submission

#### POST `/api/submit-answer` - Submit Answer
Submit an answer to a question and receive feedback.

**Request Body:**
```json
{
  "submission_id": "sub_abc123",
  "question_id": "q_xyz789",
  "answer": "factorial"  // Can be string, number, or array depending on question type
}
```

**Response (200 OK):**
```json
{
  "submission_id": "sub_abc123",
  "question_id": "q_xyz789",
  "feedback": {
    "is_correct": true,
    "explanation": "Correct! The factorial function calls itself recursively.",
    "correct_answer": null  // Only shown if answer was incorrect
  }
}
```

**Errors:**
- `404 Not Found` - Question ID not found
- `400 Bad Request` - Submission ID mismatch

### Submissions

#### GET `/api/submission/{submission_id}` - Get Submission
Retrieve a previous code submission and its questions.

**Path Parameters:**
- `submission_id` - The submission ID returned from POST `/api/submit-code`

**Response (200 OK):**
Same format as POST `/api/submit-code` response

**Errors:**
- `404 Not Found` - Submission not found

### Templates

#### GET `/api/templates` - List Templates
List all available question templates.

**Response (200 OK):**
```json
{
  "templates": [
    {
      "id": "recursive_function_detection",
      "name": "Recursive Function Detection",
      "description": "Identify which functions call themselves recursively",
      "type": "multiple_choice",
      "level": "block",
      "difficulty": "medium"
    },
    {
      "id": "variable_value_tracing",
      "name": "Variable Value Tracing",
      "description": "Trace the value of a variable at a specific execution point",
      "type": "fill_in_blank",
      "level": "atom",
      "difficulty": "easy"
    },
    {
      "id": "loop_iteration_count",
      "name": "Loop Iteration Count",
      "description": "Determine the number of iterations a loop executes",
      "type": "numeric",
      "level": "block",
      "difficulty": "medium"
    }
  ],
  "total": 3
}
```

## Question Types

### 1. Multiple Choice (`multiple_choice`)
Student selects one or more correct answers from a list.

**Response includes:**
- `answer_choices`: Array of choices with `text` and `is_correct`
- `correct_answer`: Comma-separated list of correct answers

### 2. Fill in the Blank (`fill_in_blank`)
Student provides a short text answer.

**Response includes:**
- `correct_answer`: Expected string value

### 3. Numeric (`numeric`)
Student provides a numeric answer.

**Response includes:**
- `correct_answer`: Expected number

### 4. True/False (`true_false`)
Student answers true or false.

**Response includes:**
- `correct_answer`: `true` or `false`

### 5. Short Answer (`short_answer`)
Student provides a longer text explanation.

**Response includes:**
- `correct_answer`: Sample answer or key points

### 6. Code Selection (`code_selection`)
Student selects specific lines or elements from code.

**Response includes:**
- `correct_answer`: Selected code elements

## Question Levels (Block Model)

### ATOM Level
Questions about individual language elements:
- Variable names and values
- Operators
- Literal values

**Example:** "What is the value of variable `x` on line 5?"

### BLOCK Level
Questions about code sections:
- Functions
- Loops
- Conditionals
- Code blocks

**Example:** "How many times does the loop iterate?"

### RELATIONAL Level
Questions about connections between parts:
- Function calls
- Variable usage across scopes
- Call stack depth

**Example:** "Which line declares the variable used on line 10?"

### MACRO Level
Questions about the whole program:
- Overall purpose
- Time complexity
- Algorithm choice

**Example:** "What is the time complexity of your solution?"

## Selection Strategies

### `all`
Return all generated questions (up to max_questions limit).

### `diverse`
Maximize variety across question levels and types. Uses round-robin selection to ensure balanced representation.

### `focused`
Prioritize questions based on preferences specified in `prefer_levels` and `prefer_types`.

### `adaptive`
Adapt question selection based on code complexity (future enhancement).

## Example Workflows

### Complete Workflow

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Submit code
code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
"""

response = requests.post(f"{BASE_URL}/api/submit-code", json={
    "code": code,
    "max_questions": 5,
    "strategy": "diverse"
})

data = response.json()
submission_id = data["submission_id"]
questions = data["questions"]

# 2. Display questions to student
for question in questions:
    print(question["question_text"])
    if question["answer_choices"]:
        for choice in question["answer_choices"]:
            print(f"  - {choice['text']}")

# 3. Student answers
student_answer = "factorial"  # User input

# 4. Submit answer
answer_response = requests.post(f"{BASE_URL}/api/submit-answer", json={
    "submission_id": submission_id,
    "question_id": questions[0]["id"],
    "answer": student_answer
})

feedback = answer_response.json()["feedback"]
print(f"Correct: {feedback['is_correct']}")
print(f"Explanation: {feedback['explanation']}")

# 5. Retrieve submission later
submission = requests.get(f"{BASE_URL}/api/submission/{submission_id}")
print(f"Retrieved {len(submission.json()['questions'])} questions")
```

### JavaScript/TypeScript Example

```typescript
const BASE_URL = 'http://localhost:8000';

// Submit code
const response = await fetch(`${BASE_URL}/api/submit-code`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    code: 'def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)',
    max_questions: 5
  })
});

const data = await response.json();

// Display questions
data.questions.forEach(q => {
  console.log(q.question_text);
  q.answer_choices.forEach(choice => {
    console.log(`  ${choice.is_correct ? '✓' : '○'} ${choice.text}`);
  });
});
```

## Rate Limiting

Currently no rate limiting is implemented. In production, consider:
- Rate limiting per IP
- Request size limits
- Timeout limits for code execution

## CORS

CORS is enabled for all origins in development. In production, configure `allow_origins` to specific domains:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Error Handling

All errors follow a consistent format:

```json
{
  "error": "Error Type",
  "detail": "Detailed error message",
  "status_code": 400
}
```

Common error codes:
- `400` - Bad Request (syntax error, invalid data)
- `404` - Not Found (submission/question not found)
- `422` - Unprocessable Entity (validation error)
- `500` - Internal Server Error

## Performance

Typical response times:
- Small programs (< 20 lines): 10-50ms
- Medium programs (20-100 lines): 50-200ms
- Large programs (> 100 lines): 200-500ms

Response time includes:
- Static analysis (AST parsing)
- Dynamic analysis (code execution)
- Template matching
- Question generation

## Security Considerations

### Code Execution Safety

⚠️ **Important**: The API executes submitted code using `sys.settrace()`. In production:

1. **Sandboxing**: Use containers (Docker) or VMs
2. **Resource Limits**: Set CPU/memory limits
3. **Timeout**: Code execution has 5-second timeout
4. **Input Validation**: Validate and sanitize all inputs
5. **Network Isolation**: Disable network access during execution

### Best Practices

- Run API in isolated environment
- Use authentication/authorization
- Implement rate limiting
- Log all submissions
- Monitor resource usage
- Regularly update dependencies

## Testing

### Run API Tests

```bash
# All API tests
python -m pytest tests/test_api.py -v

# Specific test
python -m pytest tests/test_api.py::TestSubmitCodeEndpoint::test_submit_valid_code -v

# With coverage
python -m pytest tests/test_api.py --cov=backend/api
```

### Manual Testing with curl

```bash
# Health check
curl http://localhost:8000/api/health

# Submit code
curl -X POST http://localhost:8000/api/submit-code \
  -H "Content-Type: application/json" \
  -d '{"code": "x = 5\ny = x * 2", "max_questions": 3}'

# List templates
curl http://localhost:8000/api/templates
```

## Deployment

### Docker

```dockerfile
FROM python:3.12

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ backend/
COPY run_api.py .

EXPOSE 8000
CMD ["python", "run_api.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./backend:/app/backend
    restart: unless-stopped
```

## Troubleshooting

### API Won't Start

```bash
# Check port 8000 is available
lsof -i :8000

# Check dependencies
pip list | grep fastapi

# Run with debug logging
uvicorn backend.api.app:app --reload --log-level debug
```

### Tests Failing

```bash
# Install test dependencies
pip install pytest httpx

# Check imports
python -c "from backend.api.app import app; print('OK')"
```

### Slow Response Times

- Check code complexity (deeply nested loops)
- Reduce max_questions
- Disable dynamic analysis for static-only questions
- Check system resources

## Support

For issues or questions:
- Check `/docs` for interactive API documentation
- Review test files for usage examples
- See `tests/test_api.py` for all endpoint examples

## License

MIT License - See LICENSE file for details
