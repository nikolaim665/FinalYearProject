import { useState } from 'react';
import Editor from '@monaco-editor/react';
import { Play, Send, Settings, Plus, Minus } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

const CodeEditor = ({ onRun, onSubmit, loading }) => {
  const { theme } = useTheme();
  const [code, setCode] = useState(`def factorial(n):
    """Calculate factorial of n"""
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
print(f"Factorial of 5 is {result}")
`);

  const [config, setConfig] = useState({
    max_questions: 5,
    strategy: 'diverse',
    test_inputs: '',
  });

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [fontSize, setFontSize] = useState(14);

  const handleRunCode = () => {
    if (onRun) {
      onRun(code);
    }
  };

  const handleSubmit = () => {
    const submissionData = {
      code,
      max_questions: config.max_questions,
      strategy: config.strategy,
    };

    if (config.test_inputs.trim()) {
      try {
        submissionData.test_inputs = JSON.parse(config.test_inputs);
      } catch (e) {
        alert('Invalid JSON in test inputs');
        return;
      }
    }

    onSubmit(submissionData);
  };

  const increaseFontSize = () => {
    setFontSize((prev) => Math.min(prev + 2, 24));
  };

  const decreaseFontSize = () => {
    setFontSize((prev) => Math.max(prev - 2, 10));
  };

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-800 transition-colors">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Code Editor
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={decreaseFontSize}
            className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition-colors"
            title="Decrease font size"
          >
            <Minus className="w-4 h-4" />
          </button>
          <span className="text-sm text-gray-600 dark:text-gray-400 w-8 text-center">
            {fontSize}
          </span>
          <button
            onClick={increaseFontSize}
            className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition-colors"
            title="Increase font size"
          >
            <Plus className="w-4 h-4" />
          </button>
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="ml-2 px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-sm flex items-center gap-2 transition-colors"
          >
            <Settings className="w-4 h-4" />
            Settings
          </button>
        </div>
      </div>

      {showAdvanced && (
        <div className="mx-4 mt-4 p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700 space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Max Questions
            </label>
            <input
              type="number"
              min="1"
              max="20"
              value={config.max_questions}
              onChange={(e) =>
                setConfig({ ...config, max_questions: parseInt(e.target.value) })
              }
              className="input-field"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Strategy
            </label>
            <select
              value={config.strategy}
              onChange={(e) => setConfig({ ...config, strategy: e.target.value })}
              className="input-field"
            >
              <option value="diverse">Diverse</option>
              <option value="focused">Focused</option>
              <option value="all">All</option>
              <option value="adaptive">Adaptive</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Test Inputs (JSON, optional)
            </label>
            <textarea
              value={config.test_inputs}
              onChange={(e) => setConfig({ ...config, test_inputs: e.target.value })}
              placeholder='[{"n": 5}, {"n": 10}]'
              className="input-field"
              rows="2"
            />
          </div>
        </div>
      )}

      <div className="flex-1 overflow-hidden m-4">
        <Editor
          height="100%"
          defaultLanguage="python"
          value={code}
          onChange={(value) => setCode(value || '')}
          theme={theme === 'dark' ? 'vs-dark' : 'vs-light'}
          options={{
            minimap: { enabled: false },
            fontSize: fontSize,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            automaticLayout: true,
            padding: { top: 16 },
          }}
        />
      </div>

      <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between bg-gray-50 dark:bg-gray-900/50">
        <div className="text-sm text-gray-500 dark:text-gray-400">
          Python
        </div>
        <div className="flex gap-2">
          {onRun && (
            <button
              onClick={handleRunCode}
              disabled={loading || !code.trim()}
              className="px-4 py-2 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Play className="w-4 h-4" />
              Run Code
            </button>
          )}
          <button
            onClick={handleSubmit}
            disabled={loading || !code.trim()}
            className="px-4 py-2 bg-primary-600 dark:bg-primary-500 text-white rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            {loading ? 'Submitting...' : 'Submit'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CodeEditor;
