import { useMutation } from '@tanstack/react-query';
import { apiService } from '../services/api';
import type { CodeSubmissionRequest, CodeSubmissionResponse } from '../types';

export const useCodeSubmission = () => {
  return useMutation<CodeSubmissionResponse, Error, CodeSubmissionRequest>({
    mutationFn: (request) => apiService.submitCode(request),
    onSuccess: (data) => {
      console.log('Code submitted successfully:', data.submission_id);
    },
    onError: (error) => {
      console.error('Error submitting code:', error);
    },
  });
};
