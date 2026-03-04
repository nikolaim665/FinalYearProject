import { useState, useEffect, useRef, useCallback } from "react";
import {
  Terminal,
  Trash2,
  Pause,
  Play,
  Download,
  ChevronDown,
} from "lucide-react";

interface LogEntry {
  timestamp: string;
  level: string;
  logger: string;
  message: string;
}

const LEVEL_STYLES: Record<string, string> = {
  DEBUG: "text-slate-400 dark:text-slate-500",
  INFO: "text-blue-600 dark:text-blue-400",
  WARNING: "text-amber-600 dark:text-amber-400",
  ERROR: "text-rose-600 dark:text-rose-400",
  CRITICAL: "text-rose-700 dark:text-rose-300 font-bold",
};

const LEVEL_BADGE: Record<string, string> = {
  DEBUG:
    "bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400",
  INFO: "bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300",
  WARNING:
    "bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300",
  ERROR: "bg-rose-100 dark:bg-rose-900/40 text-rose-700 dark:text-rose-300",
  CRITICAL:
    "bg-rose-200 dark:bg-rose-900/60 text-rose-800 dark:text-rose-200",
};

const ALL_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"];

const API_BASE = import.meta.env.VITE_API_URL || "";

export default function LogsPanel() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [paused, setPaused] = useState(false);
  const [filter, setFilter] = useState<string>("ALL");
  const [connected, setConnected] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);

  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const esRef = useRef<EventSource | null>(null);
  const pausedRef = useRef(false);
  const pendingRef = useRef<LogEntry[]>([]);

  pausedRef.current = paused;

  const flush = useCallback(() => {
    if (pendingRef.current.length === 0) return;
    const pending = pendingRef.current.splice(0);
    setLogs((prev) => [...prev, ...pending].slice(-2000));
  }, []);

  useEffect(() => {
    const url = API_BASE ? `${API_BASE}/api/logs/stream` : "/api/logs/stream";
    const es = new EventSource(url);
    esRef.current = es;

    es.onopen = () => setConnected(true);
    es.onerror = () => setConnected(false);
    es.onmessage = (ev) => {
      try {
        const entry: LogEntry = JSON.parse(ev.data);
        if (pausedRef.current) {
          pendingRef.current.push(entry);
        } else {
          setLogs((prev) => [...prev, entry].slice(-2000));
        }
      } catch {
        // ignore parse errors
      }
    };

    return () => {
      es.close();
      setConnected(false);
    };
  }, []);

  // Resume: flush pending and re-enable live
  const handleResume = () => {
    setPaused(false);
    flush();
  };

  // Auto-scroll
  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, autoScroll]);

  // Detect manual scroll up to disable auto-scroll
  const handleScroll = () => {
    const el = containerRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
    setAutoScroll(atBottom);
  };

  const clearLogs = () => {
    setLogs([]);
    pendingRef.current = [];
  };

  const downloadLogs = () => {
    const text = logs
      .map(
        (l) => `[${l.timestamp}] ${l.level.padEnd(8)} ${l.logger}: ${l.message}`
      )
      .join("\n");
    const blob = new Blob([text], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `qlc-logs-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const scrollToBottom = () => {
    setAutoScroll(true);
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const filtered =
    filter === "ALL" ? logs : logs.filter((l) => l.level === filter);

  return (
    <div className="flex flex-col h-full qlc-card overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-200 dark:border-slate-700 flex-shrink-0">
        <div className="flex items-center gap-2 flex-1">
          <Terminal className="w-4 h-4 text-indigo-500" />
          <span className="font-semibold text-slate-900 dark:text-slate-100 text-sm">
            Backend Logs
          </span>
          {/* Connection indicator */}
          <span
            className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${
              connected
                ? "bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300"
                : "bg-rose-100 dark:bg-rose-900/40 text-rose-700 dark:text-rose-300"
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                connected ? "bg-emerald-500 animate-pulse" : "bg-rose-500"
              }`}
            />
            {connected ? "Live" : "Disconnected"}
          </span>

          {paused && pendingRef.current.length > 0 && (
            <span className="text-xs text-amber-600 dark:text-amber-400">
              {pendingRef.current.length} buffered
            </span>
          )}
        </div>

        {/* Level filter */}
        <div className="flex items-center gap-1">
          {["ALL", ...ALL_LEVELS].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setFilter(lvl)}
              className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
                filter === lvl
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700"
              }`}
            >
              {lvl}
            </button>
          ))}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1">
          <button
            onClick={paused ? handleResume : () => setPaused(true)}
            className="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400 transition-colors"
            title={paused ? "Resume" : "Pause"}
          >
            {paused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
          </button>
          <button
            onClick={clearLogs}
            className="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400 transition-colors"
            title="Clear logs"
          >
            <Trash2 className="w-4 h-4" />
          </button>
          <button
            onClick={downloadLogs}
            className="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400 transition-colors"
            title="Download logs"
          >
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Log list */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto font-mono text-xs bg-slate-950 text-slate-200 p-3 space-y-0.5"
      >
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-slate-600 gap-2">
            <Terminal className="w-8 h-8 opacity-30" />
            <p className="text-sm">No log entries yet</p>
          </div>
        ) : (
          filtered.map((entry, i) => {
            const d = new Date(entry.timestamp);
            const time =
              d.toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              }) +
              "." +
              String(d.getMilliseconds()).padStart(3, "0");
            return (
              <div
                key={i}
                className={`flex gap-2 leading-5 hover:bg-white/5 rounded px-1 ${
                  LEVEL_STYLES[entry.level] ?? "text-slate-300"
                }`}
              >
                <span className="text-slate-600 shrink-0 select-none">
                  {time}
                </span>
                <span
                  className={`shrink-0 px-1 rounded text-[10px] font-semibold uppercase ${
                    LEVEL_BADGE[entry.level] ?? "bg-slate-700 text-slate-300"
                  }`}
                >
                  {entry.level}
                </span>
                <span className="text-slate-500 shrink-0 max-w-[120px] truncate">
                  {entry.logger}
                </span>
                <span className="break-all">{entry.message}</span>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>

      {/* Scroll-to-bottom button */}
      {!autoScroll && (
        <button
          onClick={scrollToBottom}
          className="absolute bottom-16 right-6 p-2 rounded-full bg-indigo-600 text-white shadow-lg hover:bg-indigo-700 transition-colors"
          title="Scroll to bottom"
        >
          <ChevronDown className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}
