import { useMutation } from '@tanstack/react-query';
import { apiService } from '../services/api';
import type { AnswerSubmissionRequest, AnswerSubmissionResponse } from '../types';

export const useAnswerSubmission = () => {
  return useMutation<AnswerSubmissionResponse, Error, AnswerSubmissionRequest>({
    mutationFn: (request) => apiService.submitAnswer(request),
    onSuccess: (data) => {
      console.log('Answer submitted successfully:', data.answer_id);
    },
    onError: (error) => {
      console.error('Error submitting answer:', error);
    },
  });
};
