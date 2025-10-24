import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import CodeEditor from '../components/CodeEditor';
import { useCodeSubmission } from '../hooks/useCodeSubmission';

const DEFAULT_CODE = `def factorial(n):
    """Calculate factorial of n"""
    if n <= 1:
        return 1
    return n * factorial(n - 1)

# Test the function
result = factorial(5)
print(f"Factorial of 5 is: {result}")
`;

const Home = () => {
  const [code, setCode] = useState<string>(DEFAULT_CODE);
  const [maxQuestions, setMaxQuestions] = useState<number>(5);
  const [strategy, setStrategy] = useState<'diverse' | 'uniform' | 'weighted'>('diverse');

  const navigate = useNavigate();
  const { mutate: submitCode, isPending, error } = useCodeSubmission();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    submitCode(
      {
        code,
        max_questions: maxQuestions,
        strategy,
      },
      {
        onSuccess: (data) => {
          // Navigate to quiz page with submission data
          navigate('/quiz', {
            state: {
              submissionId: data.submission_id,
              questions: data.questions,
              analysisSummary: data.analysis_summary,
              code: code, // Pass the code to the quiz page
            },
          });
        },
      }
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            QLC - Questions about Learners' Code
          </h1>
          <p className="text-lg text-gray-600">
            Submit your Python code and answer questions to test your understanding
          </p>
        </div>

        {/* Main Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-lg p-6 mb-6">
          {/* Code Editor */}
          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Python Code
            </label>
            <CodeEditor value={code} onChange={setCode} height="400px" />
          </div>

          {/* Settings */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {/* Max Questions */}
            <div>
              <label htmlFor="maxQuestions" className="block text-sm font-semibold text-gray-700 mb-2">
                Number of Questions
              </label>
              <input
                id="maxQuestions"
                type="number"
                min="1"
                max="20"
                value={maxQuestions}
                onChange={(e) => setMaxQuestions(parseInt(e.target.value) || 5)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Strategy */}
            <div>
              <label htmlFor="strategy" className="block text-sm font-semibold text-gray-700 mb-2">
                Question Strategy
              </label>
              <select
                id="strategy"
                value={strategy}
                onChange={(e) => setStrategy(e.target.value as 'diverse' | 'uniform' | 'weighted')}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="diverse">Diverse (Variety of question types)</option>
                <option value="uniform">Uniform (Equal distribution)</option>
                <option value="weighted">Weighted (Based on code complexity)</option>
              </select>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 font-medium">Error:</p>
              <p className="text-red-600">{error.message}</p>
            </div>
          )}

          {/* Submit Button */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isPending || !code.trim()}
              className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-md"
            >
              {isPending ? 'Analyzing Code...' : 'Generate Questions'}
            </button>
          </div>
        </form>

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-3 mb-2">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
              <h3 className="font-semibold text-gray-900">Code Analysis</h3>
            </div>
            <p className="text-sm text-gray-600">
              Your code is analyzed using both static and dynamic analysis techniques
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-3 mb-2">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="font-semibold text-gray-900">Smart Questions</h3>
            </div>
            <p className="text-sm text-gray-600">
              Questions are generated at different comprehension levels (atom, block, relational, macro)
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-3 mb-2">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="font-semibold text-gray-900">Instant Feedback</h3>
            </div>
            <p className="text-sm text-gray-600">
              Get immediate feedback on your answers with detailed explanations
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;
