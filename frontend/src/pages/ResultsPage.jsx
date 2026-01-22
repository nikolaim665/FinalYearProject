import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, Circle, AlertCircle } from 'lucide-react';
import QuestionPanel from '../components/QuestionPanel';
import ResultsSummary from '../components/ResultsSummary';
import { getSubmission, submitAnswer } from '../services/api';

const ResultsPage = () => {
  const { submissionId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [submission, setSubmission] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSubmission = async () => {
      if (!submissionId) {
        setError('No submission ID provided');
        setLoading(false);
        return;
      }

      try {
        const data = await getSubmission(submissionId);
        setSubmission(data);
      } catch (err) {
        setError(
          err.response?.data?.detail || 'Failed to load submission'
        );
      } finally {
        setLoading(false);
      }
    };

    fetchSubmission();
  }, [submissionId]);

  const handleAnswerSubmit = async (answerData) => {
    try {
      const result = await submitAnswer(answerData);
      return result;
    } catch (error) {
      throw new Error(
        error.response?.data?.detail || 'Failed to submit answer'
      );
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center transition-colors">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading results...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center transition-colors">
        <div className="text-center max-w-md mx-auto p-8">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Error Loading Results
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">{error}</p>
          <button
            onClick={() => navigate('/')}
            className="btn-primary flex items-center gap-2 mx-auto"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Code Editor
          </button>
        </div>
      </div>
    );
  }

  const answeredCount = submission?.questions?.filter(
    (q) => q.user_answer
  ).length || 0;
  const totalCount = submission?.questions?.length || 0;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span className="font-medium">Back to Editor</span>
            </button>
            <div className="flex items-center gap-4">
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Progress: {answeredCount}/{totalCount} answered
              </div>
              <div className="flex gap-1">
                {submission?.questions?.map((q, idx) => (
                  <div
                    key={idx}
                    className={`w-2 h-2 rounded-full ${
                      q.user_answer
                        ? 'bg-green-500'
                        : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                    title={`Question ${idx + 1}${
                      q.user_answer ? ' - Answered' : ' - Not answered'
                    }`}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Results Summary */}
        {submission && (
          <div className="mb-8">
            <ResultsSummary
              metadata={submission.metadata}
              analysisSummary={submission.analysis_summary}
              errors={submission.errors}
              warnings={submission.warnings}
            />
          </div>
        )}

        {/* Title */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            Generated Questions
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Answer the following questions about your code to test your understanding
          </p>
        </div>

        {/* Questions Panel */}
        <div className="max-w-4xl">
          <QuestionPanel
            questions={submission?.questions}
            submissionId={submission?.submission_id}
            onAnswerSubmit={handleAnswerSubmit}
          />
        </div>
      </main>
    </div>
  );
};

export default ResultsPage;
