import { useState, useEffect } from 'react';
import { Code2, Github, ExternalLink } from 'lucide-react';
import CodeEditor from './components/CodeEditor';
import QuestionPanel from './components/QuestionPanel';
import ResultsSummary from './components/ResultsSummary';
import { submitCode, submitAnswer, checkHealth } from './services/api';

function App() {
  const [loading, setLoading] = useState(false);
  const [submission, setSubmission] = useState(null);
  const [apiStatus, setApiStatus] = useState(null);

  useEffect(() => {
    // Check API health on mount
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-600 rounded-lg">
                <Code2 className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  QLC System
                </h1>
                <p className="text-sm text-gray-600">
                  Questions about Learners' Code
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              {apiStatus && (
                <div className="flex items-center gap-2">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      apiStatus.status === 'healthy'
                        ? 'bg-green-500'
                        : 'bg-red-500'
                    }`}
                  />
                  <span className="text-sm text-gray-600">
                    API {apiStatus.status}
                  </span>
                </div>
              )}
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-600 hover:text-gray-900"
              >
                <Github className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Introduction */}
        {!submission && (
          <div className="mb-8 card">
            <h2 className="text-xl font-bold text-gray-900 mb-3">
              Welcome to the QLC System
            </h2>
            <p className="text-gray-700 mb-3">
              This system automatically generates comprehension questions about your
              Python code to help assess program understanding beyond functional
              correctness.
            </p>
            <div className="flex items-start gap-2 text-sm text-gray-600">
              <ExternalLink className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <p>
                Based on the research paper{' '}
                <a
                  href="https://arxiv.org/abs/2103.11138"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  "Let's Ask Students About Their Programs, Automatically"
                </a>{' '}
                by Lehtinen et al. (2021)
              </p>
            </div>
          </div>
        )}

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

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Code Editor */}
          <div className="h-[600px]">
            <CodeEditor onSubmit={handleCodeSubmit} loading={loading} />
          </div>

          {/* Right Column - Questions */}
          <div className="h-[600px]">
            <QuestionPanel
              questions={submission?.questions}
              submissionId={submission?.submission_id}
              onAnswerSubmit={handleAnswerSubmit}
            />
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-16 text-center text-sm text-gray-600">
          <p>
            Questions about Learners' Code (QLC) System - Final Year Project
          </p>
          <p className="mt-1">
            Automatically generating questions to enhance program comprehension
          </p>
        </footer>
      </main>
    </div>
  );
}

export default App;
