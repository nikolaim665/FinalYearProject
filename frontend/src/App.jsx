import { useState, useEffect } from 'react';
import { Code2, Github, Sparkles, BookOpen, Zap, ArrowRight, Sun, Moon } from 'lucide-react';
import CodeEditor from './components/CodeEditor';
import QuestionPanel from './components/QuestionPanel';
import ResultsSummary from './components/ResultsSummary';
import { submitCode, submitAnswer, checkHealth } from './services/api';
import { useTheme } from './contexts/ThemeContext';

function App() {
  const [loading, setLoading] = useState(false);
  const [submission, setSubmission] = useState(null);
  const [apiStatus, setApiStatus] = useState(null);
  const { theme, toggleTheme } = useTheme();

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

  const handleCodeSubmit = async (codeData) => {
    setLoading(true);
    setSubmission(null);

    try {
      const result = await submitCode(codeData);
      setSubmission(result);
    } catch (error) {
      alert(
        'Failed to submit code: ' +
          (error.response?.data?.detail || error.message)
      );
    } finally {
      setLoading(false);
    }
  };

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

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 transition-all duration-300">
      {/* Animated gradient background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/20 dark:bg-purple-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute top-1/2 -left-40 w-80 h-80 bg-indigo-500/20 dark:bg-indigo-500/10 rounded-full blur-3xl animate-pulse animation-delay-200" />
        <div className="absolute -bottom-40 right-1/3 w-80 h-80 bg-pink-500/20 dark:bg-pink-500/10 rounded-full blur-3xl animate-pulse animation-delay-400" />
      </div>

      {/* Header */}
      <header className="relative glass-card mx-4 mt-4 lg:mx-8 lg:mt-6">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl blur opacity-75" />
                <div className="relative p-3 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl">
                  <Code2 className="w-6 h-6 text-white" />
                </div>
              </div>
              <div>
                <h1 className="text-2xl font-bold gradient-text">
                  QLC System
                </h1>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Questions about Learners' Code
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {apiStatus && (
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100 dark:bg-slate-800">
                  <div className="relative">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        apiStatus.status === 'healthy'
                          ? 'bg-emerald-500'
                          : 'bg-rose-500'
                      }`}
                    />
                    {apiStatus.status === 'healthy' && (
                      <div className="absolute inset-0 w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                    )}
                  </div>
                  <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                    {apiStatus.status === 'healthy' ? 'Connected' : 'Offline'}
                  </span>
                </div>
              )}
              <button
                onClick={toggleTheme}
                className="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400 transition-all duration-200 hover:scale-105"
                aria-label="Toggle theme"
              >
                {theme === 'light' ? (
                  <Moon className="w-5 h-5" />
                ) : (
                  <Sun className="w-5 h-5" />
                )}
              </button>
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400 transition-all duration-200 hover:scale-105"
              >
                <Github className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section / Introduction */}
        {!submission && (
          <div className="mb-8 fade-in-up">
            <div className="card p-8 relative overflow-hidden">
              {/* Decorative elements */}
              <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 rounded-full blur-3xl" />
              <div className="absolute bottom-0 left-0 w-48 h-48 bg-gradient-to-tr from-pink-500/10 to-rose-500/10 rounded-full blur-3xl" />

              <div className="relative">
                <div className="flex items-center gap-2 mb-4">
                  <Sparkles className="w-5 h-5 text-indigo-500" />
                  <span className="text-sm font-semibold text-indigo-600 dark:text-indigo-400 uppercase tracking-wide">
                    AI-Powered Learning
                  </span>
                </div>

                <h2 className="text-3xl font-bold text-slate-900 dark:text-slate-100 mb-4">
                  Welcome to the{' '}
                  <span className="gradient-text">QLC System</span>
                </h2>

                <p className="text-lg text-slate-600 dark:text-slate-400 mb-6 max-w-2xl">
                  This system automatically generates comprehension questions about your
                  Python code to help assess program understanding beyond functional
                  correctness.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="flex items-start gap-3 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50">
                    <div className="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400">
                      <Code2 className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-900 dark:text-slate-100">Submit Code</h3>
                      <p className="text-sm text-slate-600 dark:text-slate-400">
                        Write or paste your Python code
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50">
                    <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/50 text-purple-600 dark:text-purple-400">
                      <Zap className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-900 dark:text-slate-100">AI Analysis</h3>
                      <p className="text-sm text-slate-600 dark:text-slate-400">
                        GPT-powered question generation
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50">
                    <div className="p-2 rounded-lg bg-pink-100 dark:bg-pink-900/50 text-pink-600 dark:text-pink-400">
                      <BookOpen className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-900 dark:text-slate-100">Learn</h3>
                      <p className="text-sm text-slate-600 dark:text-slate-400">
                        Test your code comprehension
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                  <BookOpen className="w-4 h-4" />
                  <p>
                    Based on{' '}
                    <a
                      href="https://arxiv.org/abs/2103.11138"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-600 dark:text-indigo-400 hover:underline font-medium inline-flex items-center gap-1"
                    >
                      "Let's Ask Students About Their Programs, Automatically"
                      <ArrowRight className="w-3 h-3" />
                    </a>
                    {' '}by Lehtinen et al. (2021)
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

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

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 fade-in-up animation-delay-200">
          {/* Left Column - Code Editor */}
          <div className="h-[650px]">
            <CodeEditor onSubmit={handleCodeSubmit} loading={loading} />
          </div>

          {/* Right Column - Questions */}
          <div className="h-[650px]">
            <QuestionPanel
              questions={submission?.questions}
              submissionId={submission?.submission_id}
              onAnswerSubmit={handleAnswerSubmit}
            />
          </div>
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
              Final Year Project - Automatically generating questions to enhance program comprehension
            </p>
          </div>
        </footer>
      </main>
    </div>
  );
}

export default App;
