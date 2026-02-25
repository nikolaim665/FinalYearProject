// API types matching the FastAPI backend

export interface AnswerChoice {
  text: string;
  is_correct: boolean;
  explanation?: string;
}

export interface WrongAnswerExplanation {
  answer_text: string;
  explanation: string;
  common_misconception?: string;
}

export interface AnswerExplanationDetail {
  verified_correct_answer?: unknown;
  is_answer_verified: boolean;
  correct_answer_reasoning: string;
  code_references: string[];
  analysis_references: string[];
  wrong_answer_explanations: WrongAnswerExplanation[];
  learning_tip?: string;
  corrected_answer?: unknown;
}

export interface Question {
  id: string;
  template_id: string;
  question_text: string;
  question_type:
    | "multiple_choice"
    | "fill_in_blank"
    | "true_false"
    | "short_answer"
    | "numeric"
    | "code_selection";
  question_level: "atom" | "block" | "relational" | "macro";
  answer_type: string;
  correct_answer: unknown;
  alternative_answers: string[];
  answer_choices: AnswerChoice[];
  context: Record<string, unknown>;
  explanation?: string;
  difficulty: "easy" | "medium" | "hard";
  answer_explanation?: AnswerExplanationDetail;
}

export interface AnalysisSummary {
  total_functions?: number;
  total_variables?: number;
  total_loops?: number;
  total_conditionals?: number;
  has_recursion?: boolean;
  execution_successful?: boolean;
  max_stack_depth?: number;
}

export interface GenerationMetadata {
  total_generated: number;
  total_filtered: number;
  total_returned: number;
  applicable_templates: number;
  execution_successful: boolean;
  execution_time_ms: number;
}

export interface CodeSubmissionResponse {
  submission_id: string;
  questions: Question[];
  metadata: GenerationMetadata;
  analysis_summary: AnalysisSummary;
  errors: string[];
  warnings: string[];
}

export interface AnswerFeedback {
  is_correct: boolean;
  explanation: string;
  correct_answer?: unknown;
}

export interface AnswerSubmissionResponse {
  submission_id: string;
  question_id: string;
  feedback: AnswerFeedback;
}

export interface QuestionEvaluation {
  question_id: string;
  question_text: string;
  scores: Record<string, number>;
  overall_score: number;
  explanation: string;
  issues: string[];
  is_flagged: boolean;
}

export interface EvaluationResult {
  submission_id: string;
  question_evaluations: QuestionEvaluation[];
  aggregate: Record<string, unknown>;
  tokens_used: number;
  evaluation_time_ms: number;
}

export interface HealthStatus {
  status: "healthy" | "unhealthy";
  version?: string;
  components?: Record<string, unknown>;
}

export interface CodeSubmissionRequest {
  code: string;
  max_questions?: number;
  strategy?: string;
  test_inputs?: unknown[];
}
