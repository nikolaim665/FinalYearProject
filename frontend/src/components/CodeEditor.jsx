import { useState } from 'react';
import Editor from '@monaco-editor/react';
import { Play, Send, Settings, Plus, Minus, ChevronDown, Code2, Loader2 } from 'lucide-react';
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

  const strategies = [
    { value: 'diverse', label: 'Diverse', desc: 'Varied question types' },
    { value: 'focused', label: 'Focused', desc: 'Targeted questions' },
    { value: 'all', label: 'All', desc: 'All applicable questions' },
    { value: 'adaptive', label: 'Adaptive', desc: 'AI-selected questions' },
  ];

  return (
    <div className="h-full flex flex-col card overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-500 text-white">
            <Code2 className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              Code Editor
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Python
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Font size controls */}
          <div className="flex items-center gap-1 px-2 py-1 rounded-lg bg-slate-100 dark:bg-slate-800">
            <button
              onClick={decreaseFontSize}
              className="p-1.5 rounded-md hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400 transition-colors"
              title="Decrease font size"
            >
              <Minus className="w-3.5 h-3.5" />
            </button>
            <span className="text-xs font-medium text-slate-600 dark:text-slate-400 w-6 text-center">
              {fontSize}
            </span>
            <button
              onClick={increaseFontSize}
              className="p-1.5 rounded-md hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400 transition-colors"
              title="Increase font size"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Settings toggle */}
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
              showAdvanced
                ? 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
            }`}
          >
            <Settings className={`w-4 h-4 transition-transform duration-200 ${showAdvanced ? 'rotate-90' : ''}`} />
            Settings
            <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${showAdvanced ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      {/* Advanced Settings Panel */}
      <div
        className={`overflow-hidden transition-all duration-300 ease-out ${
          showAdvanced ? 'max-h-72 opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="p-5 bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-800">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Max Questions */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
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

            {/* Strategy */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Strategy
              </label>
              <select
                value={config.strategy}
                onChange={(e) => setConfig({ ...config, strategy: e.target.value })}
                className="input-field"
              >
                {strategies.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label} - {s.desc}
                  </option>
                ))}
              </select>
            </div>

            {/* Test Inputs */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Test Inputs (JSON, optional)
              </label>
              <textarea
                value={config.test_inputs}
                onChange={(e) => setConfig({ ...config, test_inputs: e.target.value })}
                placeholder='[{"n": 5}, {"n": 10}]'
                className="input-field font-mono text-sm"
                rows="2"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Monaco Editor */}
      <div className="flex-1 overflow-hidden">
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
            padding: { top: 16, bottom: 16 },
            fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', Consolas, monospace",
            fontLigatures: true,
            renderLineHighlight: 'all',
            cursorBlinking: 'smooth',
            cursorSmoothCaretAnimation: 'on',
            smoothScrolling: true,
            bracketPairColorization: { enabled: true },
            guides: {
              indentation: true,
              bracketPairs: true,
            },
          }}
        />
      </div>

      {/* Footer with Actions */}
      <div className="px-5 py-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="badge-slate">
              Python 3
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {code.split('\n').length} lines
            </span>
          </div>
          <div className="flex gap-3">
            {onRun && (
              <button
                onClick={handleRunCode}
                disabled={loading || !code.trim()}
                className="btn-secondary flex items-center gap-2"
              >
                <Play className="w-4 h-4" />
                Run Code
              </button>
            )}
            <button
              onClick={handleSubmit}
              disabled={loading || !code.trim()}
              className="btn-primary flex items-center gap-2 min-w-[140px] justify-center"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Generate Questions
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CodeEditor;
