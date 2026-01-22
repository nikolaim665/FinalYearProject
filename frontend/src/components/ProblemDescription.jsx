import { useState } from 'react';
import { BookOpen, TestTube, History, Clock, Tag, ChevronRight, Play } from 'lucide-react';

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

  const getDifficultyStyles = (difficulty) => {
    const styles = {
      Easy: {
        text: 'text-emerald-700 dark:text-emerald-300',
        bg: 'bg-emerald-100 dark:bg-emerald-900/50',
      },
      Medium: {
        text: 'text-amber-700 dark:text-amber-300',
        bg: 'bg-amber-100 dark:bg-amber-900/50',
      },
      Hard: {
        text: 'text-rose-700 dark:text-rose-300',
        bg: 'bg-rose-100 dark:bg-rose-900/50',
      },
    };
    return styles[difficulty] || styles.Easy;
  };

  const tabs = [
    { id: 'description', label: 'Description', icon: BookOpen },
    { id: 'testcases', label: 'Test Cases', icon: TestTube },
    { id: 'history', label: 'History', icon: History },
  ];

  const difficultyStyles = getDifficultyStyles(displayProblem.difficulty);

  return (
    <div className="h-full flex flex-col card overflow-hidden">
      {/* Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-5 py-3.5 text-sm font-medium transition-all duration-200 relative ${
                isActive
                  ? 'text-indigo-600 dark:text-indigo-400'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
              {isActive && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full" />
              )}
            </button>
          );
        })}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'description' && (
          <div className="p-6 space-y-6">
            {/* Title and Difficulty */}
            <div>
              <div className="flex items-start justify-between gap-4 mb-3">
                <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {displayProblem.title}
                </h2>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold ${difficultyStyles.bg} ${difficultyStyles.text}`}
                >
                  {displayProblem.difficulty}
                </span>
              </div>

              {/* Tags */}
              <div className="flex flex-wrap gap-2">
                {displayProblem.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded-lg text-xs font-medium"
                  >
                    <Tag className="w-3 h-3" />
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            {/* Description */}
            <div className="prose prose-slate dark:prose-invert prose-sm max-w-none">
              <p className="text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-line">
                {displayProblem.description}
              </p>
            </div>

            {/* Examples */}
            <div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4 flex items-center gap-2">
                <Play className="w-5 h-5 text-indigo-500" />
                Examples
              </h3>
              <div className="space-y-4">
                {displayProblem.examples.map((example, index) => (
                  <div
                    key={index}
                    className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700"
                  >
                    <div className="text-xs font-semibold text-slate-400 dark:text-slate-500 mb-2">
                      Example {index + 1}
                    </div>
                    <div className="space-y-2 font-mono text-sm">
                      <div className="flex items-start">
                        <span className="w-16 text-slate-500 dark:text-slate-400 shrink-0">
                          Input:
                        </span>
                        <code className="text-indigo-600 dark:text-indigo-400">
                          {example.input}
                        </code>
                      </div>
                      <div className="flex items-start">
                        <span className="w-16 text-slate-500 dark:text-slate-400 shrink-0">
                          Output:
                        </span>
                        <code className="text-emerald-600 dark:text-emerald-400">
                          {example.output}
                        </code>
                      </div>
                    </div>
                    {example.explanation && (
                      <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                          <span className="font-medium">Explanation: </span>
                          {example.explanation}
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Constraints */}
            <div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
                Constraints
              </h3>
              <ul className="space-y-2">
                {displayProblem.constraints.map((constraint, index) => (
                  <li key={index} className="flex items-start gap-3 text-slate-700 dark:text-slate-300">
                    <ChevronRight className="w-4 h-4 text-indigo-500 mt-0.5 shrink-0" />
                    <code className="text-sm font-mono">{constraint}</code>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {activeTab === 'testcases' && (
          <div className="p-6">
            <div className="text-center py-12">
              <div className="w-16 h-16 mx-auto rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4">
                <TestTube className="w-8 h-8 text-slate-400" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
                No Test Results Yet
              </h3>
              <p className="text-slate-500 dark:text-slate-400 mb-4">
                Test cases will appear here after you run your code.
              </p>
              <p className="text-sm text-slate-400 dark:text-slate-500">
                Click "Run Code" to execute test cases
              </p>
            </div>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="p-6">
            <div className="text-center py-12">
              <div className="w-16 h-16 mx-auto rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4">
                <Clock className="w-8 h-8 text-slate-400" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
                No Submissions Yet
              </h3>
              <p className="text-slate-500 dark:text-slate-400">
                Your submission history will appear here.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProblemDescription;
