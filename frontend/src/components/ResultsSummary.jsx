import {
  Activity,
  Code2,
  AlertTriangle,
  Info,
  CheckCircle,
  XCircle,
  Layers,
  GitBranch,
  Repeat,
  Clock,
  Zap,
  FileCode,
} from 'lucide-react';

const ResultsSummary = ({ metadata, analysisSummary, errors, warnings }) => {
  if (!metadata && !analysisSummary) {
    return null;
  }

  return (
    <div className="card p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-lg bg-gradient-to-r from-emerald-500 to-teal-500 text-white">
          <Activity className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100">
            Analysis Summary
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Code analysis and question generation results
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Questions Generated */}
        {metadata && (
          <>
            <div className="stat-card text-indigo-600 dark:text-indigo-400">
              <div className="flex items-center gap-2 mb-3">
                <div className="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-900/50">
                  <Zap className="w-5 h-5" />
                </div>
                <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                  Questions
                </span>
              </div>
              <p className="text-3xl font-bold text-indigo-600 dark:text-indigo-400 mb-1">
                {metadata.total_returned}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                <span className="text-emerald-600 dark:text-emerald-400">{metadata.total_generated} generated</span>
                {metadata.total_filtered > 0 && (
                  <span className="text-amber-600 dark:text-amber-400"> · {metadata.total_filtered} filtered</span>
                )}
              </p>
            </div>

            {/* Templates Applied */}
            <div className="stat-card text-purple-600 dark:text-purple-400">
              <div className="flex items-center gap-2 mb-3">
                <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/50">
                  <Layers className="w-5 h-5" />
                </div>
                <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                  Templates
                </span>
              </div>
              <p className="text-3xl font-bold text-purple-600 dark:text-purple-400 mb-1">
                {metadata.applicable_templates}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Applicable templates used
              </p>
            </div>

            {/* Execution Status */}
            <div className="stat-card">
              <div className="flex items-center gap-2 mb-3">
                <div className={`p-2 rounded-lg ${
                  metadata.execution_successful
                    ? 'bg-emerald-100 dark:bg-emerald-900/50 text-emerald-600 dark:text-emerald-400'
                    : 'bg-rose-100 dark:bg-rose-900/50 text-rose-600 dark:text-rose-400'
                }`}>
                  {metadata.execution_successful ? (
                    <CheckCircle className="w-5 h-5" />
                  ) : (
                    <XCircle className="w-5 h-5" />
                  )}
                </div>
                <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                  Execution
                </span>
              </div>
              <p className={`text-3xl font-bold mb-1 ${
                metadata.execution_successful
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : 'text-rose-600 dark:text-rose-400'
              }`}>
                {metadata.execution_successful ? 'Success' : 'Failed'}
              </p>
              {metadata.execution_time_ms !== undefined && (
                <div className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
                  <Clock className="w-3 h-3" />
                  <span>{metadata.execution_time_ms?.toFixed(2)}ms</span>
                </div>
              )}
            </div>
          </>
        )}

        {/* Code Stats */}
        {analysisSummary && (
          <div className="stat-card text-slate-600 dark:text-slate-400">
            <div className="flex items-center gap-2 mb-3">
              <div className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800">
                <FileCode className="w-5 h-5" />
              </div>
              <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                Code Stats
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {analysisSummary.total_functions > 0 && (
                <div className="flex items-center gap-1.5">
                  <Code2 className="w-3.5 h-3.5 text-indigo-500" />
                  <span className="text-slate-600 dark:text-slate-300">
                    {analysisSummary.total_functions} func
                  </span>
                </div>
              )}
              {analysisSummary.total_variables > 0 && (
                <div className="flex items-center gap-1.5">
                  <span className="w-3.5 h-3.5 text-purple-500 font-mono text-xs font-bold">x</span>
                  <span className="text-slate-600 dark:text-slate-300">
                    {analysisSummary.total_variables} vars
                  </span>
                </div>
              )}
              {analysisSummary.total_loops > 0 && (
                <div className="flex items-center gap-1.5">
                  <Repeat className="w-3.5 h-3.5 text-emerald-500" />
                  <span className="text-slate-600 dark:text-slate-300">
                    {analysisSummary.total_loops} loops
                  </span>
                </div>
              )}
              {analysisSummary.total_conditionals > 0 && (
                <div className="flex items-center gap-1.5">
                  <GitBranch className="w-3.5 h-3.5 text-amber-500" />
                  <span className="text-slate-600 dark:text-slate-300">
                    {analysisSummary.total_conditionals} if
                  </span>
                </div>
              )}
              {analysisSummary.has_recursion && (
                <div className="flex items-center gap-1.5 col-span-2">
                  <Repeat className="w-3.5 h-3.5 text-rose-500" />
                  <span className="text-rose-600 dark:text-rose-400 font-medium">
                    Recursive
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Errors and Warnings */}
      {errors && errors.length > 0 && (
        <div className="mb-4 p-4 rounded-xl bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-800">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-1.5 rounded-lg bg-rose-100 dark:bg-rose-900/50">
              <XCircle className="w-4 h-4 text-rose-600 dark:text-rose-400" />
            </div>
            <span className="text-sm font-semibold text-rose-900 dark:text-rose-100">
              Errors ({errors.length})
            </span>
          </div>
          <ul className="space-y-2">
            {errors.map((error, index) => (
              <li
                key={index}
                className="flex items-start gap-2 text-sm text-rose-800 dark:text-rose-200"
              >
                <span className="text-rose-400 mt-1">•</span>
                <span>{error}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {warnings && warnings.length > 0 && (
        <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-1.5 rounded-lg bg-amber-100 dark:bg-amber-900/50">
              <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
            </div>
            <span className="text-sm font-semibold text-amber-900 dark:text-amber-100">
              Warnings ({warnings.length})
            </span>
          </div>
          <ul className="space-y-2">
            {warnings.map((warning, index) => (
              <li
                key={index}
                className="flex items-start gap-2 text-sm text-amber-800 dark:text-amber-200"
              >
                <span className="text-amber-400 mt-1">•</span>
                <span>{warning}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default ResultsSummary;
