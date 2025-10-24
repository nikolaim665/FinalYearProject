import type { AnswerSubmissionResponse } from '../types';

interface FeedbackDisplayProps {
  feedback: AnswerSubmissionResponse;
  onNext?: () => void;
  isLastQuestion?: boolean;
}

const FeedbackDisplay = ({ feedback, onNext, isLastQuestion = false }: FeedbackDisplayProps) => {
  return (
    <div className={`rounded-lg p-6 mb-4 ${
      feedback.is_correct
        ? 'bg-green-50 border-2 border-green-200'
        : 'bg-red-50 border-2 border-red-200'
    }`}>
      {/* Result Header */}
      <div className="flex items-center gap-3 mb-4">
        {feedback.is_correct ? (
          <div className="flex items-center gap-2">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="text-2xl font-bold text-green-800">Correct!</h3>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="text-2xl font-bold text-red-800">Incorrect</h3>
          </div>
        )}

        {/* Score */}
        <div className="ml-auto">
          <span className={`text-lg font-semibold ${
            feedback.is_correct ? 'text-green-700' : 'text-red-700'
          }`}>
            Score: {feedback.score}%
          </span>
        </div>
      </div>

      {/* Feedback Message */}
      <div className="mb-4">
        <h4 className="font-semibold text-gray-700 mb-2">Feedback:</h4>
        <p className="text-gray-900">{feedback.feedback}</p>
      </div>

      {/* Correct Answer (if incorrect) */}
      {!feedback.is_correct && (
        <div className="mb-4 p-4 bg-white rounded-md border border-gray-200">
          <h4 className="font-semibold text-gray-700 mb-2">Correct Answer:</h4>
          <p className="text-gray-900 font-mono">
            {typeof feedback.correct_answer === 'object'
              ? JSON.stringify(feedback.correct_answer, null, 2)
              : String(feedback.correct_answer)}
          </p>
        </div>
      )}

      {/* Timestamps */}
      <div className="text-sm text-gray-500 mb-4">
        <p>Submitted: {new Date(feedback.submitted_at).toLocaleString()}</p>
        <p>Graded: {new Date(feedback.graded_at).toLocaleString()}</p>
      </div>

      {/* Next Button */}
      {onNext && (
        <div className="flex justify-end pt-2">
          <button
            onClick={onNext}
            className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            {isLastQuestion ? 'View Results' : 'Next Question'}
          </button>
        </div>
      )}
    </div>
  );
};

export default FeedbackDisplay;
