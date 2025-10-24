import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import CodeEditor from '../components/CodeEditor';
import ProblemDescription from '../components/ProblemDescription';
import ConsoleOutput from '../components/ConsoleOutput';
import { submitCode } from '../services/api';

const CodingPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [consoleOutput, setConsoleOutput] = useState(null);
  const [showConsole, setShowConsole] = useState(false);

  const handleRunCode = async (code) => {
    setLoading(true);
    setShowConsole(true);

    // Simulate running code
    // In a real implementation, this would call a backend API to execute the code
    setTimeout(() => {
      setConsoleOutput({
        success: true,
        stdout: 'Factorial of 5 is 120',
        executionTime: 24,
      });
      setLoading(false);
    }, 1000);
  };

  const handleSubmitCode = async (codeData) => {
    setLoading(true);
    setShowConsole(false);

    try {
      const result = await submitCode(codeData);
      // Navigate to results page with the submission ID
      navigate(`/results/${result.submission_id}`);
    } catch (error) {
      setConsoleOutput({
        error: error.response?.data?.detail || error.message,
        executionTime: 0,
      });
      setShowConsole(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-900 transition-colors">
      {/* Main Content - Split View */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side - Code Editor */}
        <div className="w-1/2 flex flex-col border-r border-gray-200 dark:border-gray-700">
          <div className="flex-1 overflow-hidden">
            <CodeEditor
              onRun={handleRunCode}
              onSubmit={handleSubmitCode}
              loading={loading}
            />
          </div>
        </div>

        {/* Right Side - Problem Description + Console */}
        <div className="w-1/2 flex flex-col">
          {/* Problem Description - Takes remaining space when console is hidden, or 50% when shown */}
          <div className={`${showConsole ? 'h-1/2' : 'flex-1'} overflow-hidden border-b border-gray-200 dark:border-gray-700`}>
            <ProblemDescription />
          </div>

          {/* Console Output - 50% height when visible */}
          {showConsole && (
            <div className="h-1/2 overflow-hidden">
              <ConsoleOutput output={consoleOutput} isVisible={showConsole} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CodingPage;
