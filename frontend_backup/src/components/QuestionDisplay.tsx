import type { Question } from '../types';

interface QuestionDisplayProps {
  question: Question;
  questionNumber: number;
  totalQuestions: number;
}

const QuestionDisplay = ({ question, questionNumber, totalQuestions }: QuestionDisplayProps) => {
  const getLevelBadgeColor = (level: string) => {
    switch (level) {
      case 'atom':
        return 'bg-blue-100 text-blue-800';
      case 'block':
        return 'bg-green-100 text-green-800';
      case 'relational':
        return 'bg-yellow-100 text-yellow-800';
      case 'macro':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeBadgeColor = (type: string) => {
    switch (type) {
      case 'multiple_choice':
        return 'bg-indigo-100 text-indigo-800';
      case 'fill_in_blank':
        return 'bg-pink-100 text-pink-800';
      case 'true_false':
        return 'bg-teal-100 text-teal-800';
      case 'short_answer':
        return 'bg-orange-100 text-orange-800';
      case 'numeric':
        return 'bg-red-100 text-red-800';
      case 'code_selection':
        return 'bg-cyan-100 text-cyan-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-700">
          Question {questionNumber} of {totalQuestions}
        </h2>
        <div className="flex gap-2">
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getLevelBadgeColor(question.question_level)}`}>
            {question.question_level}
          </span>
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getTypeBadgeColor(question.question_type)}`}>
            {question.question_type.replace('_', ' ')}
          </span>
        </div>
      </div>

      {/* Question Text */}
      <div className="mb-6">
        <p className="text-xl text-gray-900 font-medium">{question.question_text}</p>
      </div>

      {/* Context (if available) */}
      {question.context && Object.keys(question.context).length > 0 && (
        <div className="mb-4 p-4 bg-gray-50 rounded-md border border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Context:</h3>
          <pre className="text-sm text-gray-600 whitespace-pre-wrap">
            {JSON.stringify(question.context, null, 2)}
          </pre>
        </div>
      )}

      {/* Difficulty (if available) */}
      {question.difficulty && (
        <div className="text-sm text-gray-500">
          Difficulty: <span className="font-medium">{question.difficulty}</span>
        </div>
      )}
    </div>
  );
};

export default QuestionDisplay;
