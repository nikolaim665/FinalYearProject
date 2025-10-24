import { useLocation, useNavigate } from 'react-router-dom';
import type { Question, AnswerSubmissionResponse, AnalysisSummary } from '../types';

interface ResultsState {
  submissionId: string;
  questions: Question[];
  answers: Map<string, any>;
  feedback: Map<string, AnswerSubmissionResponse>;
  analysisSummary: AnalysisSummary;
}

const ResultsPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as ResultsState | null;

  if (!state) {
    navigate('/');
    return null;
  }

  const { submissionId, questions, feedback, analysisSummary } = state;

  // Calculate statistics
  const totalQuestions = questions.length;
  const answeredQuestions = feedback.size;
  const correctAnswers = Array.from(feedback.values()).filter((f) => f.is_correct).length;
  const averageScore = Array.from(feedback.values()).reduce((sum, f) => sum + f.score, 0) / answeredQuestions;

  const getPerformanceMessage = () => {
    if (averageScore >= 90) return { text: 'Excellent!', color: 'text-green-600', emoji: '🎉' };
    if (averageScore >= 70) return { text: 'Good Job!', color: 'text-blue-600', emoji: '👍' };
    if (averageScore >= 50) return { text: 'Not Bad!', color: 'text-yellow-600', emoji: '📚' };
    return { text: 'Keep Practicing!', color: 'text-red-600', emoji: '💪' };
  };

  const performance = getPerformanceMessage();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-6xl mb-4">{performance.emoji}</div>
          <h1 className={`text-4xl font-bold mb-2 ${performance.color}`}>
            {performance.text}
          </h1>
          <p className="text-lg text-gray-600">
            You've completed the quiz. Here are your results.
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-3xl font-bold text-blue-600 mb-2">{answeredQuestions}</div>
            <div className="text-sm text-gray-600">Questions Answered</div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-3xl font-bold text-green-600 mb-2">{correctAnswers}</div>
            <div className="text-sm text-gray-600">Correct Answers</div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-3xl font-bold text-purple-600 mb-2">{Math.round(averageScore)}%</div>
            <div className="text-sm text-gray-600">Average Score</div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-3xl font-bold text-orange-600 mb-2">
              {((correctAnswers / totalQuestions) * 100).toFixed(0)}%
            </div>
            <div className="text-sm text-gray-600">Success Rate</div>
          </div>
        </div>

        {/* Code Analysis Summary */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Code Analysis</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{analysisSummary.total_functions}</div>
              <div className="text-sm text-gray-600">Functions</div>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{analysisSummary.total_variables}</div>
              <div className="text-sm text-gray-600">Variables</div>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{analysisSummary.total_loops}</div>
              <div className="text-sm text-gray-600">Loops</div>
            </div>
            <div className="p-4 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {analysisSummary.has_recursion ? 'Yes' : 'No'}
              </div>
              <div className="text-sm text-gray-600">Recursion</div>
            </div>
          </div>
        </div>

        {/* Question-by-Question Breakdown */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Question Breakdown</h2>
          <div className="space-y-4">
            {questions.map((question, index) => {
              const questionFeedback = feedback.get(question.id);
              if (!questionFeedback) return null;

              return (
                <div
                  key={question.id}
                  className={`p-4 rounded-lg border-2 ${
                    questionFeedback.is_correct
                      ? 'bg-green-50 border-green-200'
                      : 'bg-red-50 border-red-200'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-gray-900">
                          Question {index + 1}
                        </span>
                        <span className="px-2 py-1 rounded text-xs font-medium bg-gray-200 text-gray-700">
                          {question.question_level}
                        </span>
                        <span className="px-2 py-1 rounded text-xs font-medium bg-gray-200 text-gray-700">
                          {question.question_type.replace('_', ' ')}
                        </span>
                      </div>
                      <p className="text-gray-700 text-sm">{question.question_text}</p>
                    </div>
                    <div className="ml-4">
                      {questionFeedback.is_correct ? (
                        <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      )}
                    </div>
                  </div>
                  <div className="mt-2 text-sm">
                    <span className={`font-semibold ${
                      questionFeedback.is_correct ? 'text-green-700' : 'text-red-700'
                    }`}>
                      Score: {questionFeedback.score}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-md"
          >
            Try Another Code
          </button>
        </div>

        {/* Submission ID */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Submission ID: {submissionId}</p>
        </div>
      </div>
    </div>
  );
};

export default ResultsPage;
