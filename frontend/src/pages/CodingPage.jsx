import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import CodeEditor from '../components/CodeEditor';
import ProblemDescription from '../components/ProblemDescription';
import ConsoleOutput from '../components/ConsoleOutput';
import Header from '../components/Header';
import { submitCode, checkHealth } from '../services/api';
import { useEffect } from 'react';

const CodingPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [consoleOutput, setConsoleOutput] = useState(null);
  const [showConsole, setShowConsole] = useState(false);
  const [apiStatus, setApiStatus] = useState(null);

  useEffect(() => {
    const checkApiHealth = async () => {
      try {
        const health = await checkHealth();
        setApiStatus(health);
      } catch (error) {
        console.error('API health check failed:', error);
        setApiStatus({ status: 'unhealthy' });
      }
    };

    checkApiHealth();
  }, []);

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
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950 transition-colors">
      {/* Animated gradient background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/20 dark:bg-purple-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute top-1/2 -left-40 w-80 h-80 bg-indigo-500/20 dark:bg-indigo-500/10 rounded-full blur-3xl animate-pulse animation-delay-200" />
        <div className="absolute -bottom-40 right-1/3 w-80 h-80 bg-pink-500/20 dark:bg-pink-500/10 rounded-full blur-3xl animate-pulse animation-delay-400" />
      </div>

      {/* Header */}
      <Header apiStatus={apiStatus} />

      {/* Main Content - Split View */}
      <div className="flex-1 flex overflow-hidden p-4 lg:p-6 gap-4 lg:gap-6 relative">
        {/* Left Side - Code Editor */}
        <div className="w-1/2 flex flex-col">
          <div className="flex-1 overflow-hidden fade-in-up">
            <CodeEditor
              onRun={handleRunCode}
              onSubmit={handleSubmitCode}
              loading={loading}
            />
          </div>
        </div>

        {/* Right Side - Problem Description + Console */}
        <div className="w-1/2 flex flex-col gap-4 lg:gap-6">
          {/* Problem Description - Takes remaining space when console is hidden, or 60% when shown */}
          <div className={`${showConsole ? 'h-[60%]' : 'flex-1'} overflow-hidden fade-in-up animation-delay-200`}>
            <ProblemDescription />
          </div>

          {/* Console Output - 40% height when visible */}
          {showConsole && (
            <div className="h-[40%] overflow-hidden fade-in-up animation-delay-300">
              <ConsoleOutput output={consoleOutput} isVisible={showConsole} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CodingPage;
