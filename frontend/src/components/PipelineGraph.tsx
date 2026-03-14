import { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  Cpu,
  MessageSquare,
  CheckSquare2,
  FileText,
  Star,
  BookOpen,
  Loader2,
  Check,
  X,
  Clock,
  Database,
  ArrowRight,
  Zap,
} from "lucide-react";
import type { NodeSummary } from "@/lib/api";

export interface NodeState {
  name: string;
  status: "pending" | "running" | "complete" | "error" | "skipped";
  summary?: NodeSummary;
  elapsedMs?: number;
  fromCache?: boolean;
}

interface PipelineGraphProps {
  nodes: NodeState[];
  fromCache: boolean;
  isActive: boolean;
}

interface NodeMeta {
  label: string;
  Icon: React.ComponentType<{ className?: string }>;
  colorClass: string;
  bgClass: string;
  ringClass: string;
  glowStyle: React.CSSProperties;
}

const NODE_META: Record<string, NodeMeta> = {
  rag_retrieve: {
    label: "RAG Retrieve",
    Icon: Database,
    colorClass: "text-teal-600 dark:text-teal-400",
    bgClass: "bg-teal-100 dark:bg-teal-900/40",
    ringClass: "ring-teal-500",
    glowStyle: { boxShadow: "0 0 0 2px rgb(20 184 166), 0 0 20px rgba(20,184,166,0.4)" },
  },
  analyzer_agent: {
    label: "Analyzer",
    Icon: Cpu,
    colorClass: "text-indigo-600 dark:text-indigo-400",
    bgClass: "bg-indigo-100 dark:bg-indigo-900/40",
    ringClass: "ring-indigo-500",
    glowStyle: { boxShadow: "0 0 0 2px rgb(99 102 241), 0 0 20px rgba(99,102,241,0.4)" },
  },
  question_agent: {
    label: "Questions",
    Icon: MessageSquare,
    colorClass: "text-purple-600 dark:text-purple-400",
    bgClass: "bg-purple-100 dark:bg-purple-900/40",
    ringClass: "ring-purple-500",
    glowStyle: { boxShadow: "0 0 0 2px rgb(168 85 247), 0 0 20px rgba(168,85,247,0.4)" },
  },
  answer_agent: {
    label: "Answers",
    Icon: CheckSquare2,
    colorClass: "text-violet-600 dark:text-violet-400",
    bgClass: "bg-violet-100 dark:bg-violet-900/40",
    ringClass: "ring-violet-500",
    glowStyle: { boxShadow: "0 0 0 2px rgb(139 92 246), 0 0 20px rgba(139,92,246,0.4)" },
  },
  explanation_agent: {
    label: "Explanations",
    Icon: FileText,
    colorClass: "text-pink-600 dark:text-pink-400",
    bgClass: "bg-pink-100 dark:bg-pink-900/40",
    ringClass: "ring-pink-500",
    glowStyle: { boxShadow: "0 0 0 2px rgb(236 72 153), 0 0 20px rgba(236,72,153,0.4)" },
  },
  judge_agent: {
    label: "Judge",
    Icon: Star,
    colorClass: "text-amber-600 dark:text-amber-400",
    bgClass: "bg-amber-100 dark:bg-amber-900/40",
    ringClass: "ring-amber-500",
    glowStyle: { boxShadow: "0 0 0 2px rgb(245 158 11), 0 0 20px rgba(245,158,11,0.4)" },
  },
};

const FALLBACK_META: NodeMeta = {
  label: "Agent",
  Icon: Zap,
  colorClass: "text-slate-600 dark:text-slate-400",
  bgClass: "bg-slate-100 dark:bg-slate-800",
  ringClass: "ring-slate-400",
  glowStyle: { boxShadow: "0 0 0 2px rgb(100 116 139), 0 0 20px rgba(100,116,139,0.3)" },
};

function formatSummary(name: string, summary: NodeSummary): string[] {
  const parts: string[] = [];
  if (name === "analyzer_agent") {
    if (summary.functions !== undefined)
      parts.push(`${summary.functions} fn${summary.functions !== 1 ? "s" : ""}`);
    if (summary.variables !== undefined) parts.push(`${summary.variables} vars`);
    if (summary.loops !== undefined) parts.push(`${summary.loops} loops`);
    if (summary.warnings !== undefined && summary.warnings > 0)
      parts.push(`${summary.warnings} warn`);
  } else if (name === "question_agent") {
    if (summary.count !== undefined)
      parts.push(`${summary.count} question${summary.count !== 1 ? "s" : ""}`);
  } else if (name === "answer_agent") {
    if (summary.count !== undefined)
      parts.push(`${summary.count} answer${summary.count !== 1 ? "s" : ""}`);
  } else if (name === "explanation_agent") {
    if (summary.count !== undefined) parts.push(`${summary.count} explained`);
  } else if (name === "judge_agent") {
    if (summary.mean_score !== undefined) parts.push(`avg ${summary.mean_score.toFixed(1)}/5`);
    if (summary.flagged !== undefined && summary.flagged > 0)
      parts.push(`${summary.flagged} flagged`);
  } else if (name === "rag_retrieve") {
    parts.push(summary.context_found ? "context found" : "no context");
  }
  return parts;
}

function NodeCard({ node }: { node: NodeState }) {
  const meta = NODE_META[node.name] ?? FALLBACK_META;
  const { label, Icon, colorClass, bgClass, glowStyle } = meta;

  const isPending = node.status === "pending";
  const isRunning = node.status === "running";
  const isComplete = node.status === "complete";
  const isError = node.status === "error";

  const summaryLines =
    isComplete && node.summary ? formatSummary(node.name, node.summary) : [];

  return (
    <div
      className={`
        relative flex flex-col items-center gap-2 p-4 rounded-2xl border transition-all duration-500
        ${isPending ? "opacity-40 border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50" : ""}
        ${isRunning ? `border-transparent ${bgClass} pipeline-node-running` : ""}
        ${isComplete ? `border-slate-200/50 dark:border-slate-700/30 ${bgClass}` : ""}
        ${isError ? "border-rose-400 bg-rose-50 dark:bg-rose-900/20" : ""}
      `}
      style={isRunning ? glowStyle : undefined}
    >
      {/* Status indicator badge */}
      <div className="absolute -top-2 -right-2">
        {isRunning && (
          <div className={`w-5 h-5 rounded-full ${bgClass} border border-white dark:border-slate-900 flex items-center justify-center`}>
            <Loader2 className={`w-3 h-3 ${colorClass} animate-spin`} />
          </div>
        )}
        {isComplete && (
          <div className="w-5 h-5 rounded-full bg-emerald-500 border border-white dark:border-slate-900 flex items-center justify-center">
            <Check className="w-3 h-3 text-white" strokeWidth={3} />
          </div>
        )}
        {isError && (
          <div className="w-5 h-5 rounded-full bg-rose-500 border border-white dark:border-slate-900 flex items-center justify-center">
            <X className="w-3 h-3 text-white" strokeWidth={3} />
          </div>
        )}
      </div>

      {/* Cache badge */}
      {isComplete && node.fromCache && (
        <div className="absolute -top-2 left-2 px-1.5 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-300 text-[9px] font-bold uppercase tracking-wide leading-tight">
          cached
        </div>
      )}

      {/* Node icon */}
      <div
        className={`p-2.5 rounded-xl transition-all duration-300 ${
          isRunning || isComplete
            ? bgClass
            : "bg-slate-100 dark:bg-slate-700/50"
        }`}
      >
        <Icon
          className={`w-5 h-5 transition-colors duration-300 ${
            isRunning || isComplete
              ? colorClass
              : "text-slate-400 dark:text-slate-500"
          }`}
        />
      </div>

      {/* Node label */}
      <span
        className={`text-xs font-semibold text-center leading-tight transition-colors duration-300 ${
          isRunning || isComplete
            ? "text-slate-900 dark:text-slate-100"
            : "text-slate-400 dark:text-slate-500"
        }`}
      >
        {label}
      </span>

      {/* Summary data */}
      {summaryLines.length > 0 && (
        <div className="flex flex-col items-center gap-0.5 mt-0.5">
          {summaryLines.map((line, i) => (
            <span key={i} className={`text-[10px] font-medium ${colorClass} text-center`}>
              {line}
            </span>
          ))}
        </div>
      )}

      {/* Elapsed time */}
      {isComplete && node.elapsedMs !== undefined && (
        <div className="flex items-center gap-1 text-[10px] text-slate-400 dark:text-slate-500">
          <Clock className="w-2.5 h-2.5" />
          <span>{(node.elapsedMs / 1000).toFixed(1)}s</span>
        </div>
      )}
    </div>
  );
}

const PipelineGraph = ({ nodes, fromCache, isActive }: PipelineGraphProps) => {
  const [collapsed, setCollapsed] = useState(false);

  const completedCount = nodes.filter((n) => n.status === "complete").length;
  const totalCount = nodes.length;

  return (
    <div className="qlc-card overflow-hidden fade-in-up">
      {/* Header — click to collapse */}
      <div
        className="flex items-center justify-between px-5 py-3 border-b border-slate-200 dark:border-slate-800 cursor-pointer select-none hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
        onClick={() => setCollapsed(!collapsed)}
      >
        <div className="flex items-center gap-3">
          {/* Pipeline icon */}
          <div className="p-1.5 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-500 text-white">
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              Agent Pipeline
              {fromCache && (
                <span className="px-1.5 py-0.5 rounded-md bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 text-[10px] font-bold uppercase tracking-wide">
                  from cache
                </span>
              )}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {isActive
                ? `Running\u2026 ${completedCount} / ${totalCount} complete`
                : `${completedCount} / ${totalCount} nodes complete`}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isActive && (
            <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-indigo-50 dark:bg-indigo-900/30">
              <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
              <span className="text-xs font-medium text-indigo-600 dark:text-indigo-400">
                Live
              </span>
            </div>
          )}
          {collapsed ? (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronUp className="w-4 h-4 text-slate-400" />
          )}
        </div>
      </div>

      {/* Graph body */}
      <div
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          collapsed ? "max-h-0" : "max-h-72"
        }`}
      >
        <div className="p-5 overflow-x-auto">
          {nodes.length === 0 ? (
            <div className="flex items-center justify-center gap-2 py-4 text-slate-400 dark:text-slate-500">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">Initialising pipeline…</span>
            </div>
          ) : (
            <div className="flex items-start gap-2 w-fit mx-auto">
              {nodes.map((node, idx) => (
                <div key={node.name} className="flex items-center gap-2">
                  <div style={{ minWidth: "100px" }}>
                    <NodeCard node={node} />
                  </div>
                  {idx < nodes.length - 1 && (
                    <ArrowRight
                      className={`w-4 h-4 flex-shrink-0 transition-colors duration-500 ${
                        node.status === "complete"
                          ? "text-indigo-400 dark:text-indigo-500"
                          : "text-slate-300 dark:text-slate-600"
                      }`}
                    />
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PipelineGraph;
