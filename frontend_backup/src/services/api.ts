import axios, { type AxiosInstance } from 'axios';
import type {
  CodeSubmissionRequest,
  CodeSubmissionResponse,
  AnswerSubmissionRequest,
  AnswerSubmissionResponse,
  HealthCheckResponse,
  Template,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000, // 30 seconds
    });

    // Request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => {
        console.log(`API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        if (error.response) {
          console.error(`API Error: ${error.response.status}`, error.response.data);
        } else if (error.request) {
          console.error('API Error: No response received', error.request);
        } else {
          console.error('API Error:', error.message);
        }
        return Promise.reject(error);
      }
    );
  }

  // Health check
  async healthCheck(): Promise<HealthCheckResponse> {
    const response = await this.client.get<HealthCheckResponse>('/api/health');
    return response.data;
  }

  // Submit code and get questions
  async submitCode(request: CodeSubmissionRequest): Promise<CodeSubmissionResponse> {
    const response = await this.client.post<CodeSubmissionResponse>(
      '/api/submit-code',
      request
    );
    return response.data;
  }

  // Submit answer and get feedback
  async submitAnswer(request: AnswerSubmissionRequest): Promise<AnswerSubmissionResponse> {
    const response = await this.client.post<AnswerSubmissionResponse>(
      '/api/submit-answer',
      request
    );
    return response.data;
  }

  // Get submission by ID
  async getSubmission(submissionId: string): Promise<CodeSubmissionResponse> {
    const response = await this.client.get<CodeSubmissionResponse>(
      `/api/submission/${submissionId}`
    );
    return response.data;
  }

  // List all submissions
  async listSubmissions(params?: {
    skip?: number;
    limit?: number;
    status?: string;
  }): Promise<CodeSubmissionResponse[]> {
    const response = await this.client.get<CodeSubmissionResponse[]>(
      '/api/submissions',
      { params }
    );
    return response.data;
  }

  // Get available templates
  async getTemplates(): Promise<Template[]> {
    const response = await this.client.get<Template[]>('/api/templates');
    return response.data;
  }
}

// Export singleton instance
export const apiService = new ApiService();

// Export class for testing
export default ApiService;
