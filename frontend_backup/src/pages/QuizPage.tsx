import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import QuestionDisplay from '../components/QuestionDisplay';
import AnswerInput from '../components/AnswerInput';
import FeedbackDisplay from '../components/FeedbackDisplay';
import CodeEditor from '../components/CodeEditor';
import { useAnswerSubmission } from '../hooks/useAnswerSubmission';
import type { Question, AnswerSubmissionResponse, AnalysisSummary } from '../types';

interface QuizState {
  submissionId: string;
  questions: Question[];
  analysisSummary: AnalysisSummary;
  code: string;
}

const QuizPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as QuizState | null;

  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Map<string, any>>(new Map());
  const [feedback, setFeedback] = useState<Map<string, AnswerSubmissionResponse>>(new Map());
  const [showFeedback, setShowFeedback] = useState(false);

  const { mutate: submitAnswer, isPending } = useAnswerSubmission();

  // Redirect if no quiz data
  useEffect(() => {
    if (!state || !state.questions || state.questions.length === 0) {
      navigate('/');
    }
  }, [state, navigate]);

  if (!state) {
    return null;
  }

  const currentQuestion = state.questions[currentQuestionIndex];
  const totalQuestions = state.questions.length;
  const isLastQuestion = currentQuestionIndex === totalQuestions - 1;
  const currentFeedback = feedback.get(currentQuestion.id);

  const handleSubmitAnswer = (answer: any) => {
    submitAnswer(
      {
        submission_id: state.submissionId,
        question_id: currentQuestion.id,
        student_answer: answer,
      },
      {
        onSuccess: (data) => {
          // Store the answer and feedback
          const newAnswers = new Map(answers);
          newAnswers.set(currentQuestion.id, answer);
          setAnswers(newAnswers);

          const newFeedback = new Map(feedback);
          newFeedback.set(currentQuestion.id, data);
          setFeedback(newFeedback);

          setShowFeedback(true);
        },
      }
    );
  };

  const handleNext = () => {
    if (isLastQuestion) {
      // Navigate to results page
      navigate('/results', {
        state: {
          submissionId: state.submissionId,
          questions: state.questions,
          answers,
          feedback,
          analysisSummary: state.analysisSummary,
        },
      });
    } else {
      // Move to next question
      setCurrentQuestionIndex(currentQuestionIndex + 1);
      setShowFeedback(false);
    }
  };

  const calculateProgress = () => {
    const answeredCount = feedback.size;
    return (answeredCount / totalQuestions) * 100;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-bold text-gray-900">Quiz</h1>
            <span className="text-sm text-gray-600">
              Submission ID: {state.submissionId.substring(0, 12)}...
            </span>
          </div>

          {/* Progress Bar */}
          <div className="mb-2">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Progress</span>
              <span>{Math.round(calculateProgress())}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${calculateProgress()}%` }}
              />
            </div>
          </div>

          {/* Analysis Summary */}
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Code Analysis:</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Functions:</span>{' '}
                <span className="font-semibold">{state.analysisSummary.total_functions}</span>
              </div>
              <div>
                <span className="text-gray-600">Variables:</span>{' '}
                <span className="font-semibold">{state.analysisSummary.total_variables}</span>
              </div>
              <div>
                <span className="text-gray-600">Loops:</span>{' '}
                <span className="font-semibold">{state.analysisSummary.total_loops}</span>
              </div>
              <div>
                <span className="text-gray-600">Recursion:</span>{' '}
                <span className="font-semibold">{state.analysisSummary.has_recursion ? 'Yes' : 'No'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Two-column layout: Code on left, Questions on right */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Panel: Code Editor (Read-only) */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Your Code</h2>
            <CodeEditor value={state.code} onChange={() => {}} readOnly height="600px" />
          </div>

          {/* Right Panel: Questions and Answers */}
          <div className="space-y-6">
            {/* Question */}
            <QuestionDisplay
              question={currentQuestion}
              questionNumber={currentQuestionIndex + 1}
              totalQuestions={totalQuestions}
            />

            {/* Answer Input or Feedback */}
            {showFeedback && currentFeedback ? (
              <FeedbackDisplay
                feedback={currentFeedback}
                onNext={handleNext}
                isLastQuestion={isLastQuestion}
              />
            ) : (
              <div className="bg-white rounded-lg shadow-md p-6">
                <AnswerInput
                  question={currentQuestion}
                  onSubmit={handleSubmitAnswer}
                  disabled={isPending}
                />
                {isPending && (
                  <div className="mt-4 text-center text-gray-600">
                    <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                    <p className="mt-2">Submitting your answer...</p>
                  </div>
                )}
              </div>
            )}

            {/* Navigation Hints */}
            <div className="text-center text-sm text-gray-600">
              <p>Question {currentQuestionIndex + 1} of {totalQuestions}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuizPage;
