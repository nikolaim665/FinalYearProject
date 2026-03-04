# QLC LangGraph Pipeline

## Flow

```
[START]
   │
   ├─ lecture_slides present ──→ [rag_retrieve] ──→ [analyzer_agent]
   │                                                       │
   └─ no slides ──────────────────────────────────→ [analyzer_agent]
                                                          │
                                          ┌───────────────┴──────────────┐
                                     success                           error
                                          │                              │
                                   [question_agent]             [error_terminal]
                                          │                              │
                                   [answer_agent]                      [END]
                                          │
                                  [explanation_agent]
                                          │
                                  [format_response]
                                          │
                                   [judge_agent]
                                          │
                                        [END]
```

## QLCState Schema

| Field | Type | Set by | Description |
|---|---|---|---|
| `source_code` | `str` | Input | Student's Python code |
| `lecture_slides` | `Optional[str]` | Input | Raw lecture slide text |
| `max_questions` | `int` | Input | Max questions to generate |
| `config` | `dict` | Input | GenerationConfig options |
| `rag_context` | `Optional[str]` | `rag_retrieve` | Top-3 retrieved lecture chunks |
| `static_analysis` | `Optional[dict]` | `analyzer_agent` | AST-based code analysis |
| `dynamic_analysis` | `Optional[dict]` | `analyzer_agent` | Runtime code analysis |
| `analysis_warnings` | `List[str]` | `analyzer_agent` | Non-fatal warnings |
| `analysis_errors` | `List[str]` | `analyzer_agent` | Fatal errors |
| `questions` | `List[dict]` | `question_agent` | Questions (no answers yet) |
| `questions_with_answers` | `List[dict]` | `answer_agent` | Questions + correct answer + 3 distractors |
| `questions_complete` | `List[dict]` | `explanation_agent` | Fully enriched with explanations |
| `evaluation` | `Optional[dict]` | `judge_agent` | Quality scores |
| `tokens_used` | `int` | Pipeline | Cumulative token count |
| `execution_time_ms` | `float` | Pipeline | Wall-clock time |
| `from_cache` | `bool` | Cache layer | Whether result was cached |

## Conditional Edges

| From | Condition | Destinations |
|---|---|---|
| `[START]` | `lecture_slides` present? | `rag_retrieve` or `analyzer_agent` |
| `analyzer_agent` | Both static + dynamic failed? | `error_terminal` or `question_agent` |
