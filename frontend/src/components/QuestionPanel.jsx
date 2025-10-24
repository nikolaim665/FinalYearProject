import { useState } from 'react';
import {
  CheckCircle,
  XCircle,
  Circle,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

const QuestionPanel = ({ questions, submissionId, onAnswerSubmit }) => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [feedback, setFeedback] = useState({});
  const [submitting, setSubmitting] = useState(false);

  if (!questions || questions.length === 0) {
    return (
      <div className="card h-full flex items-center justify-center bg-white dark:bg-gray-800 transition-colors">
        <div className="text-center text-gray-500 dark:text-gray-400">
          <AlertCircle className="w-16 h-16 mx-auto mb-4 text-gray-400 dark:text-gray-500" />
          <p className="text-lg">No questions available</p>
          <p className="text-sm mt-2">Submit code to generate questions</p>
        </div>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];
  const currentAnswer = answers[currentQuestion.id] || '';
  const currentFeedback = feedback[currentQuestion.id];

  const handleAnswerChange = (value) => {
    setAnswers({
      ...answers,
      [currentQuestion.id]: value,
    });
  };

  const handleSubmitAnswer = async () => {
    if (!currentAnswer.trim()) {
      alert('Please provide an answer');
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
      fill_in_blank: 'Fill in the Blank',
      true_false: 'True/False',
      short_answer: 'Short Answer',
      numeric: 'Numeric',
      code_selection: 'Code Selection',
    };
    return types[type] || type;
  };

  const getLevelBadgeColor = (level) => {
    const colors = {
      atom: 'bg-green-100 text-green-800',
      block: 'bg-blue-100 text-blue-800',
      relational: 'bg-purple-100 text-purple-800',
      macro: 'bg-orange-100 text-orange-800',
    };
    return colors[level] || 'bg-gray-100 text-gray-800';
  };

  const getDifficultyBadgeColor = (difficulty) => {
    const colors = {
      easy: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      hard: 'bg-red-100 text-red-800',
    };
    return colors[difficulty] || 'bg-gray-100 text-gray-800';
  };

  const renderAnswerInput = () => {
    if (currentFeedback) {
      return null; // Don't show input if already answered
    }

    switch (currentQuestion.question_type) {
      case 'multiple_choice':
        return (
          <div className="space-y-2">
            {currentQuestion.answer_choices.map((choice, index) => (
              <label
                key={index}
                className="flex items-start p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
              >
                <input
                  type="radio"
                  name="answer"
                  value={choice.text}
                  checked={currentAnswer === choice.text}
                  onChange={(e) => handleAnswerChange(e.target.value)}
                  className="mt-1 mr-3"
                />
                <span className="flex-1">{choice.text}</span>
              </label>
            ))}
          </div>
        );

      case 'true_false':
        return (
          <div className="flex gap-4">
            <label className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50 flex-1">
              <input
                type="radio"
                name="answer"
                value="true"
                checked={currentAnswer === 'true'}
                onChange={(e) => handleAnswerChange(e.target.value)}
                className="mr-3"
              />
              <span>True</span>
            </label>
            <label className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50 flex-1">
              <input
                type="radio"
                name="answer"
                value="false"
                checked={currentAnswer === 'false'}
                onChange={(e) => handleAnswerChange(e.target.value)}
                className="mr-3"
              />
              <span>False</span>
            </label>
          </div>
        );

      case 'numeric':
        return (
          <input
            type="number"
            value={currentAnswer}
            onChange={(e) => handleAnswerChange(e.target.value)}
            placeholder="Enter a number"
            className="input-field"
            step="any"
          />
        );

      default:
        return (
          <textarea
            value={currentAnswer}
            onChange={(e) => handleAnswerChange(e.target.value)}
            placeholder="Enter your answer"
            className="input-field"
            rows="3"
          />
        );
    }
  };

  return (
    <div className="card h-full flex flex-col bg-white dark:bg-gray-800 transition-colors">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100">Questions</h2>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            Question {currentQuestionIndex + 1} of {questions.length}
          </div>
        </div>

        {/* Progress indicator */}
        <div className="flex gap-2 mb-4">
          {questions.map((q, idx) => {
            const answered = feedback[q.id];
            return (
              <button
                key={q.id}
                onClick={() => setCurrentQuestionIndex(idx)}
                className="flex-1 h-2 rounded-full transition-colors"
                style={{
                  backgroundColor: answered
                    ? answered.is_correct
                      ? '#10b981'
                      : '#ef4444'
                    : idx === currentQuestionIndex
                    ? '#3b82f6'
                    : '#e5e7eb',
                }}
                title={`Question ${idx + 1}${
                  answered
                    ? answered.is_correct
                      ? ' - Correct'
                      : ' - Incorrect'
                    : ''
                }`}
              />
            );
          })}
        </div>

        {/* Question metadata */}
        <div className="flex gap-2 flex-wrap">
          <span
            className={`px-3 py-1 rounded-full text-xs font-medium ${getLevelBadgeColor(
              currentQuestion.question_level
            )}`}
          >
            {currentQuestion.question_level.toUpperCase()}
          </span>
          <span
            className={`px-3 py-1 rounded-full text-xs font-medium ${getDifficultyBadgeColor(
              currentQuestion.difficulty
            )}`}
          >
            {currentQuestion.difficulty.toUpperCase()}
          </span>
          <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            {getQuestionTypeDisplay(currentQuestion.question_type)}
          </span>
        </div>
      </div>

      {/* Question text */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">
          {currentQuestion.question_text}
        </h3>
        {currentQuestion.context && (
          <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 mb-3">
            <p className="text-sm text-gray-700">{currentQuestion.context}</p>
          </div>
        )}
      </div>

      {/* Answer input or feedback */}
      <div className="flex-1 mb-6">
        {currentFeedback ? (
          <div
            className={`p-4 rounded-lg border-2 ${
              currentFeedback.is_correct
                ? 'bg-green-50 border-green-500'
                : 'bg-red-50 border-red-500'
            }`}
          >
            <div className="flex items-start gap-3">
              {currentFeedback.is_correct ? (
                <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
              ) : (
                <XCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
              )}
              <div className="flex-1">
                <p
                  className={`font-semibold mb-2 ${
                    currentFeedback.is_correct ? 'text-green-900' : 'text-red-900'
                  }`}
                >
                  {currentFeedback.is_correct ? 'Correct!' : 'Incorrect'}
                </p>
                <p
                  className={
                    currentFeedback.is_correct ? 'text-green-800' : 'text-red-800'
                  }
                >
                  {currentFeedback.explanation}
                </p>
                {currentFeedback.correct_answer && (
                  <p className="mt-2 text-sm text-red-700">
                    <strong>Correct answer:</strong> {currentFeedback.correct_answer}
                  </p>
                )}
                <div className="mt-3">
                  <p className="text-sm font-medium text-gray-700">Your answer:</p>
                  <p className="text-sm text-gray-600">{currentAnswer}</p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Your Answer
            </label>
            {renderAnswerInput()}
            <button
              onClick={handleSubmitAnswer}
              disabled={submitting || !currentAnswer.trim()}
              className="btn-primary mt-4"
            >
              {submitting ? 'Submitting...' : 'Submit Answer'}
            </button>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex justify-between items-center pt-4 border-t">
        <button
          onClick={prevQuestion}
          disabled={currentQuestionIndex === 0}
          className="btn-secondary flex items-center gap-2"
        >
          <ChevronLeft className="w-4 h-4" />
          Previous
        </button>
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
  );
};

export default QuestionPanel;
