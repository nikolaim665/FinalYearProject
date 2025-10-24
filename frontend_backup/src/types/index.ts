// Type definitions matching backend API responses

export type QuestionLevel = 'atom' | 'block' | 'relational' | 'macro';
export type QuestionType = 'multiple_choice' | 'fill_in_blank' | 'true_false' | 'short_answer' | 'numeric' | 'code_selection';
export type SubmissionStatus = 'pending' | 'analyzed' | 'completed' | 'failed';
export type AnswerType = 'static' | 'dynamic' | 'hybrid';

export interface AnswerChoice {
  text: string;
  is_correct: boolean;
  explanation?: string;
}

export interface Question {
  id: string;
  template_id: string;
  question_text: string;
  question_type: QuestionType;
  question_level: QuestionLevel;
  answer_type: AnswerType;
  correct_answer: any;
  answer_choices?: AnswerChoice[];
  context?: Record<string, any>;
  explanation?: string;
  difficulty?: string;
}

export interface GenerationMetadata {
  total_generated: number;
  total_filtered: number;
  total_returned: number;
  applicable_templates: number;
  execution_successful: boolean;
  execution_time_ms: number;
}

export interface AnalysisSummary {
  total_functions: number;
  total_variables: number;
  total_loops: number;
  has_recursion: boolean;
  [key: string]: any;
}

export interface CodeSubmissionResponse {
  submission_id: string;
  questions: Question[];
  metadata: GenerationMetadata;
  analysis_summary: AnalysisSummary;
}

export interface CodeSubmissionRequest {
  code: string;
  max_questions?: number;
  strategy?: 'diverse' | 'uniform' | 'weighted';
  test_inputs?: Record<string, any>;
}

export interface AnswerSubmissionRequest {
  submission_id: string;
  question_id: string;
  student_answer: any;
}

export interface AnswerSubmissionResponse {
  answer_id: string;
  is_correct: boolean;
  score: number;
  feedback: string;
  correct_answer: any;
  submitted_at: string;
  graded_at: string;
}

export interface HealthCheckResponse {
  status: string;
  timestamp: string;
  components: {
    static_analyzer: string;
    dynamic_analyzer: string;
    question_generator: string;
    database: string;
  };
}

export interface Template {
  id: string;
  name: string;
  description: string;
  question_type: QuestionType;
  question_level: QuestionLevel;
  answer_type: AnswerType;
}

export interface ApiError {
  detail: string;
}

// UI State types
export interface QuizState {
  submissionId: string;
  questions: Question[];
  currentQuestionIndex: number;
  answers: Map<string, any>;
  feedback: Map<string, AnswerSubmissionResponse>;
  isLoading: boolean;
  error: string | null;
}
