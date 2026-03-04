import { useState, useRef, type ChangeEvent, type DragEvent } from "react";
import { BookOpen, Upload, X, FileText, CheckCircle, Loader2 } from "lucide-react";
import * as pdfjsLib from "pdfjs-dist";

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.mjs",
  import.meta.url
).href;

interface LectureUploaderProps {
  onLectureChange: (text: string | null) => void;
}

const LectureUploader = ({ onLectureChange }: LectureUploaderProps) => {
  const [lectureText, setLectureText] = useState<string>("");
  const [fileName, setFileName] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [showPasteArea, setShowPasteArea] = useState(false);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleTextChange = (text: string) => {
    setLectureText(text);
    onLectureChange(text.trim() || null);
  };

  const extractPdfText = async (file: File): Promise<string> => {
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    const pages: string[] = [];
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      const pageText = content.items
        .map((item) => ("str" in item ? item.str : ""))
        .join(" ");
      pages.push(pageText);
    }
    return pages.join("\n\n");
  };

  const handleFileRead = async (file: File) => {
    setFileName(file.name);
    setLoading(true);
    try {
      const text =
        file.type === "application/pdf" || file.name.endsWith(".pdf")
          ? await extractPdfText(file)
          : await file.text();
      handleTextChange(text);
    } finally {
      setLoading(false);
    }
  };

  const handleFileInput = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) void handleFileRead(file);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) void handleFileRead(file);
  };

  const handleClear = () => {
    setLectureText("");
    setFileName(null);
    setShowPasteArea(false);
    onLectureChange(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const hasContent = lectureText.trim().length > 0;
  const wordCount = hasContent ? lectureText.trim().split(/\s+/).length : 0;
  const estChunks = hasContent ? Math.ceil(lectureText.length / 1000) : 0;

  return (
    <div className="qlc-card overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <div
            className={`p-2 rounded-lg text-white transition-all duration-300 ${
              hasContent
                ? "bg-gradient-to-r from-emerald-500 to-teal-500"
                : "bg-gradient-to-r from-slate-400 to-slate-500"
            }`}
          >
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              Lecture Materials
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Optional RAG context for richer questions
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {hasContent && (
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 text-xs font-semibold">
              <CheckCircle className="w-3.5 h-3.5" />
              RAG Active
            </span>
          )}
          {hasContent && (
            <button
              onClick={handleClear}
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-900/20 transition-all duration-200"
              title="Clear lecture materials"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-5">
        {!hasContent ? (
          <div className="space-y-3">
            {/* Drop zone */}
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-200 ${
                dragOver
                  ? "border-indigo-400 bg-indigo-50 dark:bg-indigo-900/20"
                  : "border-slate-200 dark:border-slate-700 hover:border-indigo-300 dark:hover:border-indigo-600 hover:bg-slate-50 dark:hover:bg-slate-800/50"
              }`}
            >
              {loading ? (
                <Loader2 className="w-8 h-8 mx-auto mb-2 text-indigo-400 animate-spin" />
              ) : (
                <Upload className="w-8 h-8 mx-auto mb-2 text-slate-400" />
              )}
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                {loading ? "Extracting text…" : "Drop a file here or click to upload"}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                .pdf, .txt, .md, .py, or any plain-text file
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt,.md,.py,.rst,.csv,.json,.tex,.html"
                className="hidden"
                onChange={handleFileInput}
              />
            </div>

            {/* Divider */}
            <div className="flex items-center gap-2">
              <div className="flex-1 h-px bg-slate-200 dark:bg-slate-700" />
              <span className="text-xs text-slate-400">or</span>
              <div className="flex-1 h-px bg-slate-200 dark:bg-slate-700" />
            </div>

            {!showPasteArea ? (
              <button
                onClick={() => setShowPasteArea(true)}
                className="w-full py-2.5 px-4 rounded-xl border border-slate-200 dark:border-slate-700 text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all duration-200"
              >
                Paste lecture text
              </button>
            ) : (
              <textarea
                autoFocus
                placeholder="Paste your lecture slides, notes, or any relevant course material here..."
                value={lectureText}
                onChange={(e) => handleTextChange(e.target.value)}
                className="input-field font-mono text-sm resize-none w-full"
                rows={6}
              />
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {/* File info */}
            {fileName && (
              <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                <FileText className="w-4 h-4 text-indigo-500 flex-shrink-0" />
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300 truncate">
                  {fileName}
                </span>
              </div>
            )}

            {/* Stats */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 text-center">
                <p className="text-lg font-bold text-slate-900 dark:text-slate-100">
                  {wordCount.toLocaleString()}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">words</p>
              </div>
              <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 text-center">
                <p className="text-lg font-bold text-slate-900 dark:text-slate-100">
                  ~{estChunks}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">chunks</p>
              </div>
            </div>

            <p className="text-xs text-slate-500 dark:text-slate-400 text-center">
              Lecture content will be embedded and used to enrich generated questions
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default LectureUploader;
