import { Terminal, CheckCircle, XCircle, Clock, ChevronRight, AlertCircle } from 'lucide-react';

const ConsoleOutput = ({ output, isVisible }) => {
  if (!isVisible) {
    return null;
  }

  const getStatusConfig = () => {
    if (output?.success) {
      return {
        icon: CheckCircle,
        iconColor: 'text-emerald-500',
        borderColor: 'border-emerald-500',
        bgColor: 'bg-emerald-50 dark:bg-emerald-900/10',
        label: 'Success',
        labelColor: 'text-emerald-600 dark:text-emerald-400',
      };
    }
    if (output?.error) {
      return {
        icon: XCircle,
        iconColor: 'text-rose-500',
        borderColor: 'border-rose-500',
        bgColor: 'bg-rose-50 dark:bg-rose-900/10',
        label: 'Error',
        labelColor: 'text-rose-600 dark:text-rose-400',
      };
    }
    return {
      icon: Terminal,
      iconColor: 'text-slate-400',
      borderColor: 'border-slate-200 dark:border-slate-700',
      bgColor: 'bg-slate-50 dark:bg-slate-900/50',
      label: 'Console',
      labelColor: 'text-slate-600 dark:text-slate-400',
    };
  };

  const config = getStatusConfig();
  const StatusIcon = config.icon;

  return (
    <div className={`h-full flex flex-col card overflow-hidden border-l-4 ${config.borderColor}`}>
      {/* Header */}
      <div className={`flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-800 ${config.bgColor}`}>
        <div className="flex items-center gap-3">
          <StatusIcon className={`w-5 h-5 ${config.iconColor}`} />
          <div>
            <h3 className="font-semibold text-slate-900 dark:text-slate-100">
              Console
            </h3>
            <span className={`text-xs font-medium ${config.labelColor}`}>
              {config.label}
            </span>
          </div>
        </div>
        {output?.executionTime !== undefined && (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-800">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
              {output.executionTime}ms
            </span>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 bg-slate-900 dark:bg-slate-950">
        {!output && (
          <div className="flex items-center gap-3 text-slate-400">
            <Terminal className="w-5 h-5" />
            <p className="text-sm font-mono">
              Console output will appear here after running your code...
            </p>
          </div>
        )}

        {output?.stdout && (
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2">
              <ChevronRight className="w-4 h-4 text-emerald-500" />
              <span className="text-xs font-semibold text-emerald-500 uppercase tracking-wider">
                Output
              </span>
            </div>
            <pre className="font-mono text-sm text-slate-100 whitespace-pre-wrap pl-6 border-l-2 border-emerald-500/30">
              {output.stdout}
            </pre>
          </div>
        )}

        {output?.error && (
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="w-4 h-4 text-rose-500" />
              <span className="text-xs font-semibold text-rose-500 uppercase tracking-wider">
                Error
              </span>
            </div>
            <pre className="font-mono text-sm text-rose-400 whitespace-pre-wrap pl-6 border-l-2 border-rose-500/30">
              {output.error}
            </pre>
          </div>
        )}

        {output?.testResults && (
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Terminal className="w-4 h-4 text-indigo-500" />
              <span className="text-xs font-semibold text-indigo-500 uppercase tracking-wider">
                Test Results
              </span>
            </div>
            <div className="space-y-3">
              {output.testResults.map((result, index) => (
                <div
                  key={index}
                  className={`p-4 rounded-xl border ${
                    result.passed
                      ? 'border-emerald-500/30 bg-emerald-500/10'
                      : 'border-rose-500/30 bg-rose-500/10'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {result.passed ? (
                      <CheckCircle className="w-5 h-5 text-emerald-500 mt-0.5" />
                    ) : (
                      <XCircle className="w-5 h-5 text-rose-500 mt-0.5" />
                    )}
                    <div className="flex-1 font-mono text-sm space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-slate-400">Input:</span>
                        <span className="text-slate-100">{result.input}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-400">Expected:</span>
                        <span className="text-emerald-400">{result.expected}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-400">Got:</span>
                        <span className={result.passed ? 'text-emerald-400' : 'text-rose-400'}>
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
          <div className="flex items-center gap-3 text-emerald-400">
            <CheckCircle className="w-5 h-5" />
            <span className="text-sm font-mono">Code executed successfully</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ConsoleOutput;
