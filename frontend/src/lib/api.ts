import type {
  CodeSubmissionResponse,
  CodeSubmissionRequest,
  AnswerSubmissionResponse,
  EvaluationResult,
  HealthStatus,
} from "./api-types";

export type { NodeSummary } from "./api-types";

const API_BASE = import.meta.env.VITE_API_URL || "";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = API_BASE ? `${API_BASE}${path}` : path;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(
      (body as { detail?: string; error?: string }).detail ||
        (body as { error?: string }).error ||
        `API error ${res.status}`
    );
  }
  return res.json();
}

export async function checkHealth(): Promise<HealthStatus> {
  return apiFetch<HealthStatus>("/api/health");
}

export async function submitCode(
  data: CodeSubmissionRequest
): Promise<CodeSubmissionResponse> {
  return apiFetch<CodeSubmissionResponse>("/api/submit-code", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function submitAnswer(
  submissionId: string,
  questionId: string,
  answer: unknown
): Promise<AnswerSubmissionResponse> {
  return apiFetch<AnswerSubmissionResponse>("/api/submit-answer", {
    method: "POST",
    body: JSON.stringify({
      submission_id: submissionId,
      question_id: questionId,
      answer,
    }),
  });
}

export async function getSubmission(
  submissionId: string
): Promise<CodeSubmissionResponse> {
  return apiFetch<CodeSubmissionResponse>(`/api/submission/${submissionId}`);
}

export async function listTemplates(): Promise<unknown> {
  return apiFetch<unknown>("/api/templates");
}

export async function evaluateSubmission(
  submissionId: string
): Promise<EvaluationResult> {
  return apiFetch<EvaluationResult>(`/api/evaluate/${submissionId}`, {
    method: "POST",
  });
}
