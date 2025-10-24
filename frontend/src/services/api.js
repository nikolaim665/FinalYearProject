import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Health check
export const checkHealth = async () => {
  try {
    const response = await api.get('/health');
    return response.data;
  } catch (error) {
    console.error('Health check failed:', error);
    throw error;
  }
};

// Submit code and get questions
export const submitCode = async (codeData) => {
  try {
    const response = await api.post('/submit-code', codeData);
    return response.data;
  } catch (error) {
    console.error('Code submission failed:', error);
    throw error;
  }
};

// Submit an answer
export const submitAnswer = async (answerData) => {
  try {
    const response = await api.post('/submit-answer', answerData);
    return response.data;
  } catch (error) {
    console.error('Answer submission failed:', error);
    throw error;
  }
};

// Get submission by ID
export const getSubmission = async (submissionId) => {
  try {
    const response = await api.get(`/submission/${submissionId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to get submission:', error);
    throw error;
  }
};

// List all submissions
export const listSubmissions = async (params = {}) => {
  try {
    const response = await api.get('/submissions', { params });
    return response.data;
  } catch (error) {
    console.error('Failed to list submissions:', error);
    throw error;
  }
};

// List templates
export const listTemplates = async () => {
  try {
    const response = await api.get('/templates');
    return response.data;
  } catch (error) {
    console.error('Failed to list templates:', error);
    throw error;
  }
};

export default api;
