import { Activity, Code, AlertTriangle, Info } from 'lucide-react';

const ResultsSummary = ({ metadata, analysisSummary, errors, warnings }) => {
  if (!metadata && !analysisSummary) {
    return null;
  }

  return (
    <div className="card">
      <h3 className="text-xl font-bold text-gray-800 mb-4">Analysis Summary</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metadata */}
        {metadata && (
          <>
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="w-5 h-5 text-blue-600" />
                <span className="text-sm font-medium text-blue-900">Questions</span>
              </div>
              <p className="text-2xl font-bold text-blue-900">
                {metadata.total_returned}
              </p>
              <p className="text-xs text-blue-700 mt-1">
                {metadata.total_generated} generated, {metadata.total_filtered} filtered
              </p>
            </div>

            <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
              <div className="flex items-center gap-2 mb-2">
                <Code className="w-5 h-5 text-purple-600" />
                <span className="text-sm font-medium text-purple-900">Templates</span>
              </div>
              <p className="text-2xl font-bold text-purple-900">
                {metadata.applicable_templates}
              </p>
              <p className="text-xs text-purple-700 mt-1">Applicable templates</p>
            </div>

            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="flex items-center gap-2 mb-2">
                <Info className="w-5 h-5 text-green-600" />
                <span className="text-sm font-medium text-green-900">Execution</span>
              </div>
              <p className="text-2xl font-bold text-green-900">
                {metadata.execution_successful ? '✓' : '✗'}
              </p>
              <p className="text-xs text-green-700 mt-1">
                {metadata.execution_time_ms?.toFixed(2)}ms
              </p>
            </div>
          </>
        )}

        {/* Analysis Summary */}
        {analysisSummary && (
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div className="flex items-center gap-2 mb-2">
              <Code className="w-5 h-5 text-gray-600" />
              <span className="text-sm font-medium text-gray-900">Code Stats</span>
            </div>
            <div className="space-y-1 text-xs text-gray-700">
              {analysisSummary.total_functions > 0 && (
                <p>Functions: {analysisSummary.total_functions}</p>
              )}
              {analysisSummary.total_variables > 0 && (
                <p>Variables: {analysisSummary.total_variables}</p>
              )}
              {analysisSummary.total_loops > 0 && (
                <p>Loops: {analysisSummary.total_loops}</p>
              )}
              {analysisSummary.total_conditionals > 0 && (
                <p>Conditionals: {analysisSummary.total_conditionals}</p>
              )}
              {analysisSummary.has_recursion && <p>Has recursion: Yes</p>}
              {analysisSummary.max_stack_depth && (
                <p>Max stack depth: {analysisSummary.max_stack_depth}</p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Errors and Warnings */}
      {errors && errors.length > 0 && (
        <div className="mt-4 p-4 bg-red-50 rounded-lg border border-red-200">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-red-600" />
            <span className="text-sm font-medium text-red-900">Errors</span>
          </div>
          <ul className="list-disc list-inside space-y-1 text-sm text-red-800">
            {errors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {warnings && warnings.length > 0 && (
        <div className="mt-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-yellow-600" />
            <span className="text-sm font-medium text-yellow-900">Warnings</span>
          </div>
          <ul className="list-disc list-inside space-y-1 text-sm text-yellow-800">
            {warnings.map((warning, index) => (
              <li key={index}>{warning}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default ResultsSummary;
