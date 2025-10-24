import { Terminal, CheckCircle, XCircle, Clock } from 'lucide-react';

const ConsoleOutput = ({ output, isVisible }) => {
  if (!isVisible) {
    return null;
  }

  const getStatusIcon = () => {
    if (output?.success) {
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    }
    if (output?.error) {
      return <XCircle className="w-5 h-5 text-red-500" />;
    }
    return <Terminal className="w-5 h-5 text-gray-500" />;
  };

  const getStatusColor = () => {
    if (output?.success) return 'border-green-500 bg-green-50 dark:bg-green-900/20';
    if (output?.error) return 'border-red-500 bg-red-50 dark:bg-red-900/20';
    return 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900/50';
  };

  return (
    <div className={`h-full flex flex-col bg-white dark:bg-gray-800 rounded-lg border-2 ${getStatusColor()} transition-colors`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <h3 className="font-semibold text-gray-900 dark:text-gray-100">
            Console
          </h3>
        </div>
        {output?.executionTime && (
          <div className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400">
            <Clock className="w-4 h-4" />
            <span>{output.executionTime}ms</span>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {!output && (
          <div className="text-gray-500 dark:text-gray-400 text-sm">
            <p>Console output will appear here after running your code.</p>
          </div>
        )}

        {output?.stdout && (
          <div className="mb-4">
            <div className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1">
              OUTPUT
            </div>
            <pre className="font-mono text-sm text-gray-900 dark:text-gray-100 whitespace-pre-wrap">
              {output.stdout}
            </pre>
          </div>
        )}

        {output?.error && (
          <div className="mb-4">
            <div className="text-xs font-semibold text-red-600 dark:text-red-400 mb-1">
              ERROR
            </div>
            <pre className="font-mono text-sm text-red-700 dark:text-red-300 whitespace-pre-wrap">
              {output.error}
            </pre>
          </div>
        )}

        {output?.testResults && (
          <div>
            <div className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2">
              TEST RESULTS
            </div>
            <div className="space-y-2">
              {output.testResults.map((result, index) => (
                <div
                  key={index}
                  className={`p-3 rounded-lg border ${
                    result.passed
                      ? 'border-green-300 bg-green-50 dark:bg-green-900/20'
                      : 'border-red-300 bg-red-50 dark:bg-red-900/20'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {result.passed ? (
                      <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400 mt-0.5" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-600 dark:text-red-400 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <div className="font-mono text-sm">
                        <span className="text-gray-600 dark:text-gray-400">
                          Input:{' '}
                        </span>
                        <span className="text-gray-900 dark:text-gray-100">
                          {result.input}
                        </span>
                      </div>
                      <div className="font-mono text-sm">
                        <span className="text-gray-600 dark:text-gray-400">
                          Expected:{' '}
                        </span>
                        <span className="text-gray-900 dark:text-gray-100">
                          {result.expected}
                        </span>
                      </div>
                      <div className="font-mono text-sm">
                        <span className="text-gray-600 dark:text-gray-400">
                          Got:{' '}
                        </span>
                        <span className="text-gray-900 dark:text-gray-100">
                          {result.actual}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {output?.success && !output.stdout && !output.testResults && (
          <div className="text-green-600 dark:text-green-400 text-sm">
            <CheckCircle className="w-5 h-5 inline mr-2" />
            Code executed successfully
          </div>
        )}
      </div>
    </div>
  );
};

export default ConsoleOutput;
