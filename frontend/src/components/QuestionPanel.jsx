import { useState } from 'react';
import {
  CheckCircle,
  XCircle,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  HelpCircle,
  Loader2,
  Sparkles,
  Trophy,
  Target,
  Lightbulb,
  Code,
  BookOpen,
  ChevronDown,
  ChevronUp,
  FileText,
  Database,
} from 'lucide-react';

const QuestionPanel = ({ questions, submissionId, onAnswerSubmit }) => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [feedback, setFeedback] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [showDetailedExplanation, setShowDetailedExplanation] = useState({});

  // Calculate score
  const answeredQuestions = Object.keys(feedback).length;
  const correctAnswers = Object.values(feedback).filter(f => f.is_correct).length;

  if (!questions || questions.length === 0) {
    return (
      <div className="card h-full flex items-center justify-center p-8">
        <div className="text-center max-w-sm">
          <div className="relative mb-6">
            <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-indigo-100 to-purple-100 dark:from-indigo-900/30 dark:to-purple-900/30 flex items-center justify-center">
              <HelpCircle className="w-10 h-10 text-indigo-500 dark:text-indigo-400" />
            </div>
            <div className="absolute -bottom-1 -right-1 w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 blur-xl" />
          </div>
          <h3 className="text-xl font-semibold text-slate-900 dark:text-slate-100 mb-2">
            No Questions Yet
          </h3>
          <p className="text-slate-500 dark:text-slate-400 mb-4">
            Submit your Python code to generate AI-powered comprehension questions.
          </p>
          <div className="flex items-center justify-center gap-2 text-sm text-indigo-600 dark:text-indigo-400">
            <Sparkles className="w-4 h-4" />
            <span>Powered by GPT</span>
          </div>
        </div>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];
  const currentAnswer = answers[currentQuestion.id] ?? '';
  const currentFeedback = feedback[currentQuestion.id];

  const handleAnswerChange = (value) => {
    setAnswers({
      ...answers,
      [currentQuestion.id]: value,
    });
  };

  const handleSubmitAnswer = async () => {
    if (currentAnswer === '' || (typeof currentAnswer === 'string' && !currentAnswer.trim())) {
      return;
    }

    setSubmitting(true);
    try {
      const result = await onAnswerSubmit({
        submission_id: submissionId,
        question_id: currentQuestion.id,
        answer: currentAnswer,
      });

      setFeedback({
        ...feedback,
        [currentQuestion.id]: result.feedback,
      });
    } catch (error) {
      alert('Failed to submit answer: ' + error.message);
    } finally {
      setSubmitting(false);
    }
  };

  const nextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const prevQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const getQuestionTypeDisplay = (type) => {
    const types = {
      multiple_choice: 'Multiple Choice',
      fill_in_blank: 'Fill in Blank',
      true_false: 'True/False',
      short_answer: 'Short Answer',
      numeric: 'Numeric',
      code_selection: 'Code Selection',
    };
    return types[type] || type;
  };

  const getLevelBadgeClass = (level) => {
    const classes = {
      atom: 'badge-success',
      block: 'badge-blue',
      relational: 'badge-purple',
      macro: 'badge-warning',
    };
    return classes[level] || 'badge-slate';
  };

  const getDifficultyBadgeClass = (difficulty) => {
    const classes = {
      easy: 'badge-success',
      medium: 'badge-warning',
      hard: 'badge-danger',
    };
    return classes[difficulty] || 'badge-slate';
  };

  const renderAnswerInput = () => {
    if (currentFeedback) {
      return null;
    }

    switch (currentQuestion.question_type) {
      case 'multiple_choice':
        return (
          <div className="space-y-3">
            {currentQuestion.answer_choices?.map((choice, index) => (
              <label
                key={index}
                className={`flex items-start p-4 rounded-xl cursor-pointer transition-all duration-200 border-2 ${
                  currentAnswer === choice.text
                    ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                    : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-800/50'
                }`}
              >
                <input
                  type="radio"
                  name="answer"
                  value={choice.text}
                  checked={currentAnswer === choice.text}
                  onChange={(e) => handleAnswerChange(e.target.value)}
                  className="mt-1 mr-4 w-4 h-4 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="flex-1 text-slate-700 dark:text-slate-300">{choice.text}</span>
              </label>
            ))}
          </div>
        );

      case 'true_false':
        return (
          <div className="grid grid-cols-2 gap-4">
            {['true', 'false'].map((value) => (
              <label
                key={value}
                className={`flex items-center justify-center p-4 rounded-xl cursor-pointer transition-all duration-200 border-2 ${
                  currentAnswer === value
                    ? value === 'true'
                      ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20'
                      : 'border-rose-500 bg-rose-50 dark:bg-rose-900/20'
                    : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
                }`}
              >
                <input
                  type="radio"
                  name="answer"
                  value={value}
                  checked={currentAnswer === value}
                  onChange={(e) => handleAnswerChange(e.target.value)}
                  className="sr-only"
                />
                <span className={`font-semibold capitalize ${
                  currentAnswer === value
                    ? value === 'true'
                      ? 'text-emerald-700 dark:text-emerald-300'
                      : 'text-rose-700 dark:text-rose-300'
                    : 'text-slate-600 dark:text-slate-400'
                }`}>
                  {value}
                </span>
              </label>
            ))}
          </div>
        );

      case 'numeric':
        return (
          <input
            type="number"
            value={currentAnswer}
            onChange={(e) => handleAnswerChange(e.target.value)}
            placeholder="Enter a number"
            className="input-field text-lg"
            step="any"
          />
        );

      default:
        return (
          <textarea
            value={currentAnswer}
            onChange={(e) => handleAnswerChange(e.target.value)}
            placeholder="Type your answer here..."
            className="input-field resize-none"
            rows="4"
          />
        );
    }
  };

  return (
    <div className="card h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 text-white">
              <Target className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                Questions
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Question {currentQuestionIndex + 1} of {questions.length}
              </p>
            </div>
          </div>

          {/* Score Display */}
          {answeredQuestions > 0 && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100 dark:bg-slate-800">
              <Trophy className={`w-4 h-4 ${correctAnswers === answeredQuestions ? 'text-amber-500' : 'text-slate-400'}`} />
              <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                {correctAnswers}/{answeredQuestions}
              </span>
            </div>
          )}
        </div>

        {/* Progress indicator */}
        <div className="flex gap-1.5">
          {questions.map((q, idx) => {
            const answered = feedback[q.id];
            return (
              <button
                key={q.id}
                onClick={() => setCurrentQuestionIndex(idx)}
                className={`flex-1 h-2 rounded-full transition-all duration-300 ${
                  answered
                    ? answered.is_correct
                      ? 'bg-emerald-500'
                      : 'bg-rose-500'
                    : idx === currentQuestionIndex
                    ? 'bg-indigo-500'
                    : 'bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600'
                }`}
                title={`Question ${idx + 1}${
                  answered ? (answered.is_correct ? ' - Correct' : ' - Incorrect') : ''
                }`}
              />
            );
          })}
        </div>
      </div>

      {/* Question Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Question metadata badges */}
        <div className="flex gap-2 flex-wrap mb-4">
          <span className={getLevelBadgeClass(currentQuestion.question_level)}>
            {currentQuestion.question_level}
          </span>
          <span className={getDifficultyBadgeClass(currentQuestion.difficulty)}>
            {currentQuestion.difficulty}
          </span>
          <span className="badge-slate">
            {getQuestionTypeDisplay(currentQuestion.question_type)}
          </span>
        </div>

        {/* Question text */}
        <div className="mb-6">
          <h3 className="text-xl font-semibold text-slate-900 dark:text-slate-100 leading-relaxed">
            {currentQuestion.question_text}
          </h3>
          {currentQuestion.context && typeof currentQuestion.context === 'string' && (
            <div className="mt-4 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700">
              <p className="text-sm text-slate-600 dark:text-slate-400 font-mono">
                {currentQuestion.context}
              </p>
            </div>
          )}
        </div>

        {/* Answer input or feedback */}
        {currentFeedback ? (
          <div className="space-y-4">
            {/* Main feedback card */}
            <div
              className={`p-5 rounded-2xl border-2 transition-all duration-300 ${
                currentFeedback.is_correct
                  ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-500'
                  : 'bg-rose-50 dark:bg-rose-900/20 border-rose-500'
              }`}
            >
              <div className="flex items-start gap-4">
                <div className={`p-2 rounded-xl ${
                  currentFeedback.is_correct
                    ? 'bg-emerald-500'
                    : 'bg-rose-500'
                }`}>
                  {currentFeedback.is_correct ? (
                    <CheckCircle className="w-6 h-6 text-white" />
                  ) : (
                    <XCircle className="w-6 h-6 text-white" />
                  )}
                </div>
                <div className="flex-1">
                  <p className={`text-lg font-semibold mb-2 ${
                    currentFeedback.is_correct
                      ? 'text-emerald-900 dark:text-emerald-100'
                      : 'text-rose-900 dark:text-rose-100'
                  }`}>
                    {currentFeedback.is_correct ? 'Correct!' : 'Incorrect'}
                  </p>

                  {currentFeedback.explanation && (
                    <div className={`p-3 rounded-lg mb-3 ${
                      currentFeedback.is_correct
                        ? 'bg-emerald-100 dark:bg-emerald-900/30'
                        : 'bg-rose-100 dark:bg-rose-900/30'
                    }`}>
                      <div className="flex items-start gap-2">
                        <Lightbulb className={`w-4 h-4 mt-0.5 ${
                          currentFeedback.is_correct
                            ? 'text-emerald-600 dark:text-emerald-400'
                            : 'text-rose-600 dark:text-rose-400'
                        }`} />
                        <p className={`text-sm ${
                          currentFeedback.is_correct
                            ? 'text-emerald-800 dark:text-emerald-200'
                            : 'text-rose-800 dark:text-rose-200'
                        }`}>
                          {currentFeedback.explanation}
                        </p>
                      </div>
                    </div>
                  )}

                  {currentFeedback.correct_answer && !currentFeedback.is_correct && (
                    <p className="text-sm text-rose-700 dark:text-rose-300 mb-2">
                      <span className="font-medium">Correct answer:</span> {String(currentFeedback.correct_answer)}
                    </p>
                  )}

                  <div className="text-sm">
                    <span className="font-medium text-slate-600 dark:text-slate-400">Your answer: </span>
                    <span className="text-slate-700 dark:text-slate-300">{String(currentAnswer)}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Detailed Explanation Section (from Answer Explainer LLM) */}
            {currentQuestion.answer_explanation && (
              <div className="border border-slate-200 dark:border-slate-700 rounded-2xl overflow-hidden">
                <button
                  onClick={() => setShowDetailedExplanation({
                    ...showDetailedExplanation,
                    [currentQuestion.id]: !showDetailedExplanation[currentQuestion.id]
                  })}
                  className="w-full px-5 py-3 flex items-center justify-between bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-indigo-500" />
                    <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                      Detailed Explanation
                    </span>
                  </div>
                  {showDetailedExplanation[currentQuestion.id] ? (
                    <ChevronUp className="w-4 h-4 text-slate-400" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  )}
                </button>

                {showDetailedExplanation[currentQuestion.id] && (
                  <div className="p-5 space-y-4 bg-white dark:bg-slate-900">
                    {/* Why the correct answer is correct */}
                    {currentQuestion.answer_explanation.correct_answer_reasoning && (
                      <div>
                        <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-2 flex items-center gap-2">
                          <CheckCircle className="w-4 h-4 text-emerald-500" />
                          Why the correct answer is correct
                        </h4>
                        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed pl-6">
                          {currentQuestion.answer_explanation.correct_answer_reasoning}
                        </p>
                      </div>
                    )}

                    {/* Code References */}
                    {currentQuestion.answer_explanation.code_references?.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-2 flex items-center gap-2">
                          <Code className="w-4 h-4 text-blue-500" />
                          Code References
                        </h4>
                        <ul className="space-y-1 pl-6">
                          {currentQuestion.answer_explanation.code_references.map((ref, idx) => (
                            <li key={idx} className="text-sm text-slate-600 dark:text-slate-400 font-mono bg-slate-50 dark:bg-slate-800 px-3 py-1.5 rounded-lg">
                              {ref}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Analysis References */}
                    {currentQuestion.answer_explanation.analysis_references?.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-2 flex items-center gap-2">
                          <Database className="w-4 h-4 text-purple-500" />
                          Analysis References
                        </h4>
                        <ul className="space-y-1 pl-6">
                          {currentQuestion.answer_explanation.analysis_references.map((ref, idx) => (
                            <li key={idx} className="text-sm text-slate-600 dark:text-slate-400 bg-purple-50 dark:bg-purple-900/20 px-3 py-1.5 rounded-lg">
                              {ref}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Wrong Answer Explanations */}
                    {currentQuestion.answer_explanation.wrong_answer_explanations?.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-2 flex items-center gap-2">
                          <XCircle className="w-4 h-4 text-rose-500" />
                          Why other answers are wrong
                        </h4>
                        <div className="space-y-2 pl-6">
                          {currentQuestion.answer_explanation.wrong_answer_explanations.map((we, idx) => (
                            <div key={idx} className="bg-rose-50 dark:bg-rose-900/10 border border-rose-200 dark:border-rose-800 rounded-lg p-3">
                              <p className="text-sm font-medium text-rose-800 dark:text-rose-200 mb-1">
                                "{we.answer_text}"
                              </p>
                              <p className="text-sm text-rose-700 dark:text-rose-300">
                                {we.explanation}
                              </p>
                              {we.common_misconception && (
                                <p className="text-xs text-rose-500 dark:text-rose-400 mt-1 italic">
                                  Common misconception: {we.common_misconception}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Learning Tip */}
                    {currentQuestion.answer_explanation.learning_tip && (
                      <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3">
                        <h4 className="text-sm font-semibold text-amber-800 dark:text-amber-200 mb-1 flex items-center gap-2">
                          <Lightbulb className="w-4 h-4" />
                          Learning Tip
                        </h4>
                        <p className="text-sm text-amber-700 dark:text-amber-300 pl-6">
                          {currentQuestion.answer_explanation.learning_tip}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
              Your Answer
            </label>
            {renderAnswerInput()}
            <button
              onClick={handleSubmitAnswer}
              disabled={submitting || currentAnswer === '' || (typeof currentAnswer === 'string' && !currentAnswer.trim())}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Checking...
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4" />
                  Submit Answer
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Navigation Footer */}
      <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50">
        <div className="flex justify-between items-center">
          <button
            onClick={prevQuestion}
            disabled={currentQuestionIndex === 0}
            className="btn-secondary flex items-center gap-2"
          >
            <ChevronLeft className="w-4 h-4" />
            Previous
          </button>

          <div className="flex items-center gap-1">
            {questions.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentQuestionIndex(idx)}
                className={`w-2 h-2 rounded-full transition-all duration-200 ${
                  idx === currentQuestionIndex
                    ? 'w-6 bg-indigo-500'
                    : 'bg-slate-300 dark:bg-slate-600 hover:bg-slate-400 dark:hover:bg-slate-500'
                }`}
              />
            ))}
          </div>

          <button
            onClick={nextQuestion}
            disabled={currentQuestionIndex === questions.length - 1}
            className="btn-secondary flex items-center gap-2"
          >
            Next
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default QuestionPanel;
