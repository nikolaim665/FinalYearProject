import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, AlertCircle, Loader2, Sparkles, Target, Code2, FlaskConical, CheckCircle2, XCircle, ChevronDown, ChevronUp } from 'lucide-react';
import QuestionPanel from '../components/QuestionPanel';
import ResultsSummary from '../components/ResultsSummary';
import Header from '../components/Header';
import { getSubmission, submitAnswer, checkHealth, evaluateSubmission } from '../services/api';

const SCORE_LABELS = {
  accuracy: 'Accuracy',
  clarity: 'Clarity',
  pedagogical_value: 'Pedagogy',
  code_specificity: 'Specificity',
  difficulty_calibration: 'Difficulty',
};

const ScoreBar = ({ score }) => {
  const pct = ((score - 1) / 4) * 100;
  const color =
    score >= 4 ? 'bg-emerald-500' : score >= 3 ? 'bg-amber-400' : 'bg-rose-500';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-bold w-4 text-right text-slate-700 dark:text-slate-300">{score}</span>
    </div>
  );
};

const QuestionEvalCard = ({ evaluation, index }) => {
  const [open, setOpen] = useState(false);
  return (
    <div className={`border rounded-xl p-4 ${evaluation.is_flagged ? 'border-rose-300 dark:border-rose-700 bg-rose-50 dark:bg-rose-950/30' : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800'}`}>
      <div className="flex items-start justify-between gap-3 cursor-pointer" onClick={() => setOpen(!open)}>
        <div className="flex items-center gap-2 flex-1 min-w-0">
          {evaluation.is_flagged
            ? <XCircle className="w-4 h-4 text-rose-500 shrink-0" />
            : <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />}
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300 truncate">
            Q{index}: {evaluation.question_text}
          </span>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <span className={`text-sm font-bold ${evaluation.overall_score >= 4 ? 'text-emerald-600' : evaluation.overall_score >= 3 ? 'text-amber-600' : 'text-rose-600'}`}>
            {evaluation.overall_score.toFixed(1)}
          </span>
          {evaluation.is_flagged && (
            <span className="text-xs font-semibold text-rose-600 dark:text-rose-400 bg-rose-100 dark:bg-rose-900/50 px-2 py-0.5 rounded-full">FLAGGED</span>
          )}
          {open ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
        </div>
      </div>

      {open && (
        <div className="mt-4 space-y-3 border-t border-slate-100 dark:border-slate-700 pt-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2">
            {Object.entries(SCORE_LABELS).map(([key, label]) => (
              <div key={key}>
                <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                  <span>{label}</span>
                </div>
                <ScoreBar score={evaluation.scores[key] ?? 0} />
              </div>
            ))}
          </div>
          {evaluation.explanation && (
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">{evaluation.explanation}</p>
          )}
          {evaluation.issues.length > 0 && (
            <ul className="space-y-1">
              {evaluation.issues.map((issue, i) => (
                <li key={i} className="text-xs text-rose-600 dark:text-rose-400 flex items-start gap-1">
                  <span className="mt-0.5 shrink-0">•</span><span>{issue}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};

const EvaluationPanel = ({ submissionId }) => {
  const [evalState, setEvalState] = useState('idle'); // idle | loading | done | error
  const [evalResult, setEvalResult] = useState(null);
  const [evalError, setEvalError] = useState(null);

  const handleEvaluate = async () => {
    setEvalState('loading');
    setEvalError(null);
    try {
      const result = await evaluateSubmission(submissionId);
      setEvalResult(result);
      setEvalState('done');
    } catch (err) {
      setEvalError(err.response?.data?.detail || err.message || 'Evaluation failed');
      setEvalState('error');
    }
  };

  const agg = evalResult?.aggregate;

  return (
    <div className="mt-8 border border-indigo-200 dark:border-indigo-800 rounded-2xl overflow-hidden">
      <div className="px-6 py-4 bg-indigo-50 dark:bg-indigo-950/40 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FlaskConical className="w-5 h-5 text-indigo-500" />
          <span className="font-semibold text-slate-900 dark:text-slate-100">LLM Judge — Question Quality Evaluation</span>
        </div>
        {evalState !== 'done' && (
          <button
            onClick={handleEvaluate}
            disabled={evalState === 'loading'}
            className="btn-primary flex items-center gap-2 text-sm"
          >
            {evalState === 'loading' && <Loader2 className="w-4 h-4 animate-spin" />}
            {evalState === 'loading' ? 'Evaluating…' : 'Run Evaluation'}
          </button>
        )}
      </div>

      {evalState === 'idle' && (
        <div className="px-6 py-5 text-sm text-slate-500 dark:text-slate-400">
          Click <strong>Run Evaluation</strong> to have the LLM judge score every generated question on accuracy, clarity, pedagogical value, specificity and difficulty calibration.
        </div>
      )}

      {evalState === 'loading' && (
        <div className="px-6 py-10 flex flex-col items-center gap-3 text-slate-500 dark:text-slate-400">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
          <p className="text-sm">Evaluating questions… (one LLM call per question)</p>
        </div>
      )}

      {evalState === 'error' && (
        <div className="px-6 py-5 flex items-center gap-3 text-rose-600 dark:text-rose-400 text-sm">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{evalError}</span>
        </div>
      )}

      {evalState === 'done' && evalResult && (
        <div className="px-6 py-5 space-y-4">
          {/* Aggregate stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: 'Overall', value: agg.mean_overall?.toFixed(2) },
              { label: 'Accuracy', value: agg.mean_accuracy?.toFixed(2) },
              { label: 'Pedagogy', value: agg.mean_pedagogical_value?.toFixed(2) },
              { label: 'Flagged', value: `${agg.questions_flagged}/${agg.total_questions}` },
            ].map(({ label, value }) => (
              <div key={label} className="text-center px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800">
                <div className="text-lg font-bold text-slate-900 dark:text-slate-100">{value}</div>
                <div className="text-xs text-slate-500 dark:text-slate-400">{label}</div>
              </div>
            ))}
          </div>

          {/* Per-question evaluations */}
          <div className="space-y-2">
            {evalResult.question_evaluations.map((ev, idx) => (
              <QuestionEvalCard key={ev.question_id} evaluation={ev} index={idx + 1} />
            ))}
          </div>

          <p className="text-xs text-slate-400 dark:text-slate-500 text-right">
            {evalResult.tokens_used} tokens · {(evalResult.evaluation_time_ms / 1000).toFixed(1)}s
          </p>
        </div>
      )}
    </div>
  );
};

const ResultsPage = () => {
  const { submissionId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [submission, setSubmission] = useState(null);
  const [error, setError] = useState(null);
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

  useEffect(() => {
    const fetchSubmission = async () => {
      if (!submissionId) {
        setError('No submission ID provided');
        setLoading(false);
        return;
      }

      try {
        const data = await getSubmission(submissionId);
        setSubmission(data);
      } catch (err) {
        setError(
          err.response?.data?.detail || 'Failed to load submission'
        );
      } finally {
        setLoading(false);
      }
    };

    fetchSubmission();
  }, [submissionId]);

  const handleAnswerSubmit = async (answerData) => {
    try {
      const result = await submitAnswer(answerData);
      return result;
    } catch (error) {
      throw new Error(
        error.response?.data?.detail || 'Failed to submit answer'
      );
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center transition-colors">
        {/* Animated gradient background */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/20 dark:bg-purple-500/10 rounded-full blur-3xl animate-pulse" />
          <div className="absolute top-1/2 -left-40 w-80 h-80 bg-indigo-500/20 dark:bg-indigo-500/10 rounded-full blur-3xl animate-pulse animation-delay-200" />
        </div>

        <div className="text-center relative">
          <div className="relative mb-6">
            <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center pulse-glow">
              <Loader2 className="w-10 h-10 text-white animate-spin" />
            </div>
          </div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100 mb-2">
            Loading Results
          </h2>
          <p className="text-slate-500 dark:text-slate-400">
            Fetching your submission data...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center transition-colors">
        {/* Animated gradient background */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-rose-500/20 dark:bg-rose-500/10 rounded-full blur-3xl animate-pulse" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-amber-500/20 dark:bg-amber-500/10 rounded-full blur-3xl animate-pulse animation-delay-200" />
        </div>

        <div className="text-center max-w-md mx-auto p-8 card relative fade-in-up">
          <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-rose-100 to-amber-100 dark:from-rose-900/30 dark:to-amber-900/30 flex items-center justify-center mb-6">
            <AlertCircle className="w-10 h-10 text-rose-500" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
            Error Loading Results
          </h2>
          <p className="text-slate-600 dark:text-slate-400 mb-6">{error}</p>
          <button
            onClick={() => navigate('/')}
            className="btn-primary flex items-center gap-2 mx-auto"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Code Editor
          </button>
        </div>
      </div>
    );
  }

  const answeredCount = submission?.questions?.filter(
    (q) => q.user_answer
  ).length || 0;
  const totalCount = submission?.questions?.length || 0;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 transition-colors">
      {/* Animated gradient background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/20 dark:bg-purple-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute top-1/2 -left-40 w-80 h-80 bg-indigo-500/20 dark:bg-indigo-500/10 rounded-full blur-3xl animate-pulse animation-delay-200" />
        <div className="absolute -bottom-40 right-1/3 w-80 h-80 bg-pink-500/20 dark:bg-pink-500/10 rounded-full blur-3xl animate-pulse animation-delay-400" />
      </div>

      {/* Header */}
      <Header apiStatus={apiStatus} />

      {/* Sub-header with navigation */}
      <div className="relative glass-card mx-4 mt-4 lg:mx-8">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span className="font-medium">Back to Editor</span>
            </button>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-800">
                <Target className="w-4 h-4 text-indigo-500" />
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Progress: {answeredCount}/{totalCount}
                </span>
              </div>
              <div className="flex gap-1">
                {submission?.questions?.map((q, idx) => (
                  <div
                    key={idx}
                    className={`w-2 h-2 rounded-full transition-colors ${
                      q.user_answer
                        ? 'bg-emerald-500'
                        : 'bg-slate-300 dark:bg-slate-600'
                    }`}
                    title={`Question ${idx + 1}${
                      q.user_answer ? ' - Answered' : ' - Not answered'
                    }`}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Results Summary */}
        {submission && (
          <div className="mb-8 fade-in-up">
            <ResultsSummary
              metadata={submission.metadata}
              analysisSummary={submission.analysis_summary}
              errors={submission.errors}
              warnings={submission.warnings}
            />
          </div>
        )}

        {/* Title */}
        <div className="mb-6 fade-in-up animation-delay-100">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-5 h-5 text-indigo-500" />
            <span className="text-sm font-semibold text-indigo-600 dark:text-indigo-400 uppercase tracking-wide">
              AI-Generated Assessment
            </span>
          </div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
            Code Comprehension Questions
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-2">
            Test your understanding by answering the following questions about your code
          </p>
        </div>

        {/* Questions Panel */}
        <div className="max-w-4xl fade-in-up animation-delay-200">
          <QuestionPanel
            questions={submission?.questions}
            submissionId={submission?.submission_id}
            onAnswerSubmit={handleAnswerSubmit}
          />
        </div>

        {/* LLM Judge Evaluation Panel */}
        {submission?.submission_id && (
          <div className="max-w-4xl fade-in-up animation-delay-300">
            <EvaluationPanel submissionId={submission.submission_id} />
          </div>
        )}

        {/* Footer */}
        <footer className="mt-16 text-center fade-in">
          <div className="divider mb-8" />
          <div className="flex flex-col items-center gap-2">
            <div className="flex items-center gap-2 text-slate-400 dark:text-slate-500">
              <Code2 className="w-4 h-4" />
              <span className="text-sm font-medium">QLC System</span>
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Automatically generating questions to enhance program comprehension
            </p>
          </div>
        </footer>
      </main>
    </div>
  );
};

export default ResultsPage;
