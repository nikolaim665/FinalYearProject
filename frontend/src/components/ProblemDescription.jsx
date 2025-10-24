import { useState } from 'react';
import { BookOpen, TestTube, History } from 'lucide-react';

const ProblemDescription = ({ problem }) => {
  const [activeTab, setActiveTab] = useState('description');

  const defaultProblem = {
    title: 'Calculate Factorial',
    difficulty: 'Easy',
    description: `Write a Python function that calculates the factorial of a given number n. The factorial of a number is the product of all positive integers less than or equal to that number.

For example, the factorial of 5 (denoted as 5!) is calculated as:
5! = 5 × 4 × 3 × 2 × 1 = 120

Your function should handle edge cases such as n = 0 (which should return 1) and negative numbers.`,
    examples: [
      {
        input: 'factorial(5)',
        output: '120',
        explanation: '5! = 5 × 4 × 3 × 2 × 1 = 120',
      },
      {
        input: 'factorial(0)',
        output: '1',
        explanation: 'By definition, 0! = 1',
      },
      {
        input: 'factorial(3)',
        output: '6',
        explanation: '3! = 3 × 2 × 1 = 6',
      },
    ],
    constraints: [
      '0 ≤ n ≤ 1000',
      'n is an integer',
      'Function should be efficient for large values',
    ],
    tags: ['Math', 'Recursion', 'Iteration'],
  };

  const displayProblem = problem || defaultProblem;

  const getDifficultyColor = (difficulty) => {
    const colors = {
      Easy: 'text-green-600 dark:text-green-400',
      Medium: 'text-yellow-600 dark:text-yellow-400',
      Hard: 'text-red-600 dark:text-red-400',
    };
    return colors[difficulty] || 'text-gray-600 dark:text-gray-400';
  };

  const tabs = [
    { id: 'description', label: 'Description', icon: BookOpen },
    { id: 'testcases', label: 'Test Cases', icon: TestTube },
    { id: 'history', label: 'History', icon: History },
  ];

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 transition-colors">
      {/* Tabs */}
      <div className="flex border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors relative ${
                activeTab === tab.id
                  ? 'text-primary-600 dark:text-primary-400'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
              {activeTab === tab.id && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600 dark:bg-primary-400" />
              )}
            </button>
          );
        })}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'description' && (
          <div className="space-y-6">
            {/* Title and Difficulty */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                {displayProblem.title}
              </h2>
              <span
                className={`text-sm font-medium ${getDifficultyColor(
                  displayProblem.difficulty
                )}`}
              >
                {displayProblem.difficulty}
              </span>
            </div>

            {/* Description */}
            <div className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
              {displayProblem.description}
            </div>

            {/* Examples */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Examples
              </h3>
              <div className="space-y-4">
                {displayProblem.examples.map((example, index) => (
                  <div
                    key={index}
                    className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700"
                  >
                    <div className="font-mono text-sm mb-2">
                      <span className="text-gray-600 dark:text-gray-400">
                        Input:{' '}
                      </span>
                      <span className="text-gray-900 dark:text-gray-100">
                        {example.input}
                      </span>
                    </div>
                    <div className="font-mono text-sm mb-2">
                      <span className="text-gray-600 dark:text-gray-400">
                        Output:{' '}
                      </span>
                      <span className="text-gray-900 dark:text-gray-100">
                        {example.output}
                      </span>
                    </div>
                    {example.explanation && (
                      <div className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                        <span className="font-medium">Explanation: </span>
                        {example.explanation}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Constraints */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Constraints
              </h3>
              <ul className="space-y-2 text-gray-700 dark:text-gray-300">
                {displayProblem.constraints.map((constraint, index) => (
                  <li key={index} className="flex items-start">
                    <span className="mr-2">•</span>
                    <span className="font-mono text-sm">{constraint}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Tags */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Tags
              </h3>
              <div className="flex flex-wrap gap-2">
                {displayProblem.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full text-sm"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'testcases' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Test Cases
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Test cases will appear here after you run your code.
            </p>
            <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Click "Run Code" to execute test cases
              </p>
            </div>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Submission History
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Your submission history will appear here.
            </p>
            <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                No submissions yet
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProblemDescription;
