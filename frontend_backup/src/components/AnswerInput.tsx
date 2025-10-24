import { useState } from 'react';
import type { Question } from '../types';

interface AnswerInputProps {
  question: Question;
  onSubmit: (answer: any) => void;
  disabled?: boolean;
}

const AnswerInput = ({ question, onSubmit, disabled = false }: AnswerInputProps) => {
  const [answer, setAnswer] = useState<any>(null);
  const [textInput, setTextInput] = useState<string>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Submit button clicked!', { questionType: question.question_type, textInput, answer });

    let submittedAnswer = answer;

    // Convert text input for numeric questions
    if (question.question_type === 'numeric') {
      submittedAnswer = parseFloat(textInput) || 0;
    } else if (question.question_type === 'short_answer' || question.question_type === 'fill_in_blank') {
      submittedAnswer = textInput;
    }

    console.log('Submitting answer:', submittedAnswer);
    onSubmit(submittedAnswer);
  };

  const renderInput = () => {
    switch (question.question_type) {
      case 'multiple_choice':
        return (
          <div className="space-y-3">
            {question.answer_choices?.map((choice, index) => (
              <label
                key={index}
                className={`flex items-center p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  answer === choice.text
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-blue-300'
                } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <input
                  type="radio"
                  name="answer"
                  value={choice.text}
                  checked={answer === choice.text}
                  onChange={(e) => setAnswer(e.target.value)}
                  disabled={disabled}
                  className="mr-3 h-4 w-4 text-blue-600"
                />
                <span className="text-gray-900">{choice.text}</span>
              </label>
            ))}
          </div>
        );

      case 'true_false':
        return (
          <div className="flex gap-4">
            <button
              type="button"
              onClick={() => setAnswer(true)}
              disabled={disabled}
              className={`flex-1 py-4 px-6 border-2 rounded-lg font-medium transition-all ${
                answer === true
                  ? 'border-green-500 bg-green-50 text-green-700'
                  : 'border-gray-200 hover:border-green-300 text-gray-700'
              } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              True
            </button>
            <button
              type="button"
              onClick={() => setAnswer(false)}
              disabled={disabled}
              className={`flex-1 py-4 px-6 border-2 rounded-lg font-medium transition-all ${
                answer === false
                  ? 'border-red-500 bg-red-50 text-red-700'
                  : 'border-gray-200 hover:border-red-300 text-gray-700'
              } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              False
            </button>
          </div>
        );

      case 'numeric':
        return (
          <input
            type="number"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            disabled={disabled}
            placeholder="Enter a number"
            className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 disabled:opacity-50"
          />
        );

      case 'short_answer':
      case 'fill_in_blank':
        return (
          <textarea
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            disabled={disabled}
            placeholder="Enter your answer"
            rows={4}
            className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 disabled:opacity-50 resize-none"
          />
        );

      case 'code_selection':
        return (
          <div className="space-y-3">
            {question.answer_choices?.map((choice, index) => (
              <label
                key={index}
                className={`flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  answer === choice.text
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-blue-300'
                } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <input
                  type="radio"
                  name="answer"
                  value={choice.text}
                  checked={answer === choice.text}
                  onChange={(e) => setAnswer(e.target.value)}
                  disabled={disabled}
                  className="mr-3 mt-1 h-4 w-4 text-blue-600"
                />
                <code className="text-gray-900 font-mono text-sm whitespace-pre-wrap">
                  {choice.text}
                </code>
              </label>
            ))}
          </div>
        );

      default:
        return (
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            disabled={disabled}
            placeholder="Enter your answer"
            className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 disabled:opacity-50"
          />
        );
    }
  };

  const isAnswerProvided = () => {
    if (question.question_type === 'numeric' ||
        question.question_type === 'short_answer' ||
        question.question_type === 'fill_in_blank') {
      return textInput.trim() !== '';
    }
    return answer !== null;
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {renderInput()}

      <div className="flex justify-end pt-4">
        <button
          type="submit"
          disabled={disabled || !isAnswerProvided()}
          className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Submit Answer
        </button>
      </div>
    </form>
  );
};

export default AnswerInput;
