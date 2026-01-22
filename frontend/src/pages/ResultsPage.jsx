import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, AlertCircle, Loader2, Sparkles, Target, Code2 } from 'lucide-react';
import QuestionPanel from '../components/QuestionPanel';
import ResultsSummary from '../components/ResultsSummary';
import Header from '../components/Header';
import { getSubmission, submitAnswer, checkHealth } from '../services/api';

const ResultsPage = () => {
  const { submissionId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [submission, setSubmission] = useState(null);
  const [error, setError] = useState(null);
  const [apiStatus, setApiStatus] = useState(null);

  useEffect(() => {
    const checkApiHealth = async () => {
      try {
        const health = await checkHealth();
        setApiStatus(health);
      } catch (error) {
        console.error('API health check failed:', error);
        setApiStatus({ status: 'unhealthy' });
      }
    };

    checkApiHealth();
  }, []);

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
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center transition-colors">
        {/* Animated gradient background */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/20 dark:bg-purple-500/10 rounded-full blur-3xl animate-pulse" />
          <div className="absolute top-1/2 -left-40 w-80 h-80 bg-indigo-500/20 dark:bg-indigo-500/10 rounded-full blur-3xl animate-pulse animation-delay-200" />
        </div>

        <div className="text-center relative">
          <div className="relative mb-6">
            <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center pulse-glow">
              <Loader2 className="w-10 h-10 text-white animate-spin" />
            </div>
          </div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100 mb-2">
            Loading Results
          </h2>
          <p className="text-slate-500 dark:text-slate-400">
            Fetching your submission data...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center transition-colors">
        {/* Animated gradient background */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-rose-500/20 dark:bg-rose-500/10 rounded-full blur-3xl animate-pulse" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-amber-500/20 dark:bg-amber-500/10 rounded-full blur-3xl animate-pulse animation-delay-200" />
        </div>

        <div className="text-center max-w-md mx-auto p-8 card relative fade-in-up">
          <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-rose-100 to-amber-100 dark:from-rose-900/30 dark:to-amber-900/30 flex items-center justify-center mb-6">
            <AlertCircle className="w-10 h-10 text-rose-500" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
            Error Loading Results
          </h2>
          <p className="text-slate-600 dark:text-slate-400 mb-6">{error}</p>
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
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 transition-colors">
      {/* Animated gradient background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/20 dark:bg-purple-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute top-1/2 -left-40 w-80 h-80 bg-indigo-500/20 dark:bg-indigo-500/10 rounded-full blur-3xl animate-pulse animation-delay-200" />
        <div className="absolute -bottom-40 right-1/3 w-80 h-80 bg-pink-500/20 dark:bg-pink-500/10 rounded-full blur-3xl animate-pulse animation-delay-400" />
      </div>

      {/* Header */}
      <Header apiStatus={apiStatus} />

      {/* Sub-header with navigation */}
      <div className="relative glass-card mx-4 mt-4 lg:mx-8">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span className="font-medium">Back to Editor</span>
            </button>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-800">
                <Target className="w-4 h-4 text-indigo-500" />
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Progress: {answeredCount}/{totalCount}
                </span>
              </div>
              <div className="flex gap-1">
                {submission?.questions?.map((q, idx) => (
                  <div
                    key={idx}
                    className={`w-2 h-2 rounded-full transition-colors ${
                      q.user_answer
                        ? 'bg-emerald-500'
                        : 'bg-slate-300 dark:bg-slate-600'
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
      <main className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Results Summary */}
        {submission && (
          <div className="mb-8 fade-in-up">
            <ResultsSummary
              metadata={submission.metadata}
              analysisSummary={submission.analysis_summary}
              errors={submission.errors}
              warnings={submission.warnings}
            />
          </div>
        )}

        {/* Title */}
        <div className="mb-6 fade-in-up animation-delay-100">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-5 h-5 text-indigo-500" />
            <span className="text-sm font-semibold text-indigo-600 dark:text-indigo-400 uppercase tracking-wide">
              AI-Generated Assessment
            </span>
          </div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
            Code Comprehension Questions
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-2">
            Test your understanding by answering the following questions about your code
          </p>
        </div>

        {/* Questions Panel */}
        <div className="max-w-4xl fade-in-up animation-delay-200">
          <QuestionPanel
            questions={submission?.questions}
            submissionId={submission?.submission_id}
            onAnswerSubmit={handleAnswerSubmit}
          />
        </div>

        {/* Footer */}
        <footer className="mt-16 text-center fade-in">
          <div className="divider mb-8" />
          <div className="flex flex-col items-center gap-2">
            <div className="flex items-center gap-2 text-slate-400 dark:text-slate-500">
              <Code2 className="w-4 h-4" />
              <span className="text-sm font-medium">QLC System</span>
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Automatically generating questions to enhance program comprehension
            </p>
          </div>
        </footer>
      </main>
    </div>
  );
};

export default ResultsPage;
