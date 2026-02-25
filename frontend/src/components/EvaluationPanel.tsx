import { useState } from "react";
import {
  AlertTriangle,
  BarChart3,
  Loader2,
  Star,
  TrendingUp,
  CheckCircle2,
} from "lucide-react";
import type { Question, QuestionEvaluation } from "@/lib/api-types";
import { evaluateSubmission } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface EvaluationPanelProps {
  questions: Question[];
  submissionId: string;
}

const EvaluationPanel = ({ questions, submissionId }: EvaluationPanelProps) => {
  const { toast } = useToast();
  const [evaluations, setEvaluations] = useState<QuestionEvaluation[]>([]);
  const [loading, setLoading] = useState(false);
  const [evaluated, setEvaluated] = useState(false);

  if (questions.length === 0) return null;

  const diffCounts = {
    easy: questions.filter((q) => q.difficulty === "easy").length,
    medium: questions.filter((q) => q.difficulty === "medium").length,
    hard: questions.filter((q) => q.difficulty === "hard").length,
  };

  const levelCounts = {
    atom: questions.filter((q) => q.question_level === "atom").length,
    block: questions.filter((q) => q.question_level === "block").length,
    relational: questions.filter((q) => q.question_level === "relational").length,
    macro: questions.filter((q) => q.question_level === "macro").length,
  };

  const handleEvaluate = async () => {
    setLoading(true);
    try {
      const result = await evaluateSubmission(submissionId);
      setEvaluations(result.question_evaluations);
      setEvaluated(true);
      toast({
        title: "Evaluation complete",
        description: `Evaluated ${result.question_evaluations.length} questions`,
      });
    } catch (e) {
      toast({
        title: "Evaluation failed",
        description: (e as Error).message || "Failed to evaluate questions",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const avgScore =
    evaluations.length > 0
      ? evaluations.reduce((sum, ev) => sum + ev.overall_score, 0) /
        evaluations.length
      : null;

  return (
    <div className="space-y-4">
      {/* Summary Card */}
      <div className="qlc-card p-5">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="w-5 h-5 text-indigo-500" />
          <h3 className="font-semibold text-slate-900 dark:text-slate-100">
            Question Summary
          </h3>
        </div>

        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="rounded-xl bg-indigo-50 dark:bg-indigo-900/30 p-3 text-center">
            <p className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
              {questions.length}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400">Questions</p>
          </div>
          <div className="rounded-xl bg-purple-50 dark:bg-purple-900/30 p-3 text-center">
            <TrendingUp className="w-4 h-4 text-purple-500 mx-auto mb-1" />
            <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {new Set(questions.map((q) => q.question_type)).size}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400">Types</p>
          </div>
          <div className="rounded-xl bg-emerald-50 dark:bg-emerald-900/30 p-3 text-center">
            <CheckCircle2 className="w-4 h-4 text-emerald-500 mx-auto mb-1" />
            <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
              {Object.values(levelCounts).filter((c) => c > 0).length}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400">Levels</p>
          </div>
        </div>

        {/* Difficulty breakdown */}
        <div className="space-y-2 mb-4">
          <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
            Difficulty
          </p>
          {(["easy", "medium", "hard"] as const).map((diff) => (
            <div key={diff} className="flex items-center gap-2">
              <span className="w-16 text-xs capitalize text-slate-500 dark:text-slate-400">
                {diff}
              </span>
              <div className="flex-1 h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    diff === "easy"
                      ? "bg-emerald-500"
                      : diff === "medium"
                        ? "bg-amber-500"
                        : "bg-rose-500"
                  }`}
                  style={{
                    width: `${(diffCounts[diff] / questions.length) * 100}%`,
                  }}
                />
              </div>
              <span className="w-6 text-xs text-slate-500 dark:text-slate-400 text-right">
                {diffCounts[diff]}
              </span>
            </div>
          ))}
        </div>

        {/* Level breakdown */}
        <div className="space-y-2">
          <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
            Question Level
          </p>
          {(["atom", "block", "relational", "macro"] as const).map((level) =>
            levelCounts[level] > 0 ? (
              <div key={level} className="flex items-center justify-between">
                <span className="text-xs capitalize text-slate-500 dark:text-slate-400">
                  {level}
                </span>
                <span className="badge-slate text-xs">{levelCounts[level]}</span>
              </div>
            ) : null
          )}
        </div>
      </div>

      {/* LLM Judge Card */}
      <div className="qlc-card p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Star className="w-5 h-5 text-amber-500" />
            <h3 className="font-semibold text-slate-900 dark:text-slate-100">
              Quality Evaluation
            </h3>
          </div>
          {avgScore !== null && (
            <div className="flex items-center gap-1">
              <span
                className={`text-lg font-bold ${
                  avgScore >= 4
                    ? "text-emerald-600 dark:text-emerald-400"
                    : avgScore >= 3
                      ? "text-amber-600 dark:text-amber-400"
                      : "text-rose-600 dark:text-rose-400"
                }`}
              >
                {avgScore.toFixed(1)}
              </span>
              <span className="text-xs text-slate-400">/5 avg</span>
            </div>
          )}
        </div>

        {!evaluated ? (
          <div className="text-center py-4">
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
              Run the LLM judge to evaluate question quality on accuracy, clarity,
              pedagogical value, and more.
            </p>
            <button
              onClick={handleEvaluate}
              disabled={loading}
              className="btn-primary flex items-center gap-2 mx-auto"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Evaluating...
                </>
              ) : (
                <>
                  <Star className="w-4 h-4" />
                  Evaluate Questions
                </>
              )}
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {evaluations.map((ev) => (
              <div
                key={ev.question_id}
                className={`rounded-xl border p-3 space-y-1.5 ${
                  ev.is_flagged
                    ? "border-rose-200 dark:border-rose-800 bg-rose-50 dark:bg-rose-900/10"
                    : "border-slate-200 dark:border-slate-700"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-xs text-slate-700 dark:text-slate-300 line-clamp-1">
                    {ev.question_text}
                  </p>
                  <div className="flex items-center gap-1 shrink-0">
                    {ev.is_flagged && (
                      <AlertTriangle className="h-3 w-3 text-rose-500" />
                    )}
                    <span
                      className={`text-sm font-bold ${
                        ev.overall_score >= 4
                          ? "text-emerald-600 dark:text-emerald-400"
                          : ev.overall_score >= 3
                            ? "text-amber-600 dark:text-amber-400"
                            : "text-rose-600 dark:text-rose-400"
                      }`}
                    >
                      {ev.overall_score.toFixed(1)}
                    </span>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1">
                  {Object.entries(ev.scores).map(([dim, score]) => (
                    <span
                      key={dim}
                      className="badge-slate text-[10px] capitalize"
                    >
                      {dim.replace(/_/g, " ")}: {score}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default EvaluationPanel;
