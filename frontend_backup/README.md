# QLC Frontend

React + TypeScript frontend for the Questions about Learners' Code (QLC) system.

## Features

- **Code Editor**: Monaco Editor for Python code submission
- **Interactive Quiz**: Answer questions about your code
- **Real-time Feedback**: Instant grading and explanations
- **Progress Tracking**: Visual progress through the quiz
- **Results Dashboard**: Detailed performance analytics

## Tech Stack

- **React 19** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **TailwindCSS** - Utility-first CSS
- **React Query** - API state management
- **React Router** - Client-side routing
- **Monaco Editor** - Code editor component
- **Axios** - HTTP client

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── CodeEditor.tsx
│   ├── QuestionDisplay.tsx
│   ├── AnswerInput.tsx
│   └── FeedbackDisplay.tsx
├── pages/              # Page components
│   ├── Home.tsx
│   ├── QuizPage.tsx
│   └── ResultsPage.tsx
├── hooks/              # Custom React hooks
│   ├── useCodeSubmission.ts
│   └── useAnswerSubmission.ts
├── services/           # API service layer
│   └── api.ts
├── types/              # TypeScript type definitions
│   └── index.ts
├── App.tsx             # Main app component with routing
└── main.tsx            # Application entry point
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at http://localhost:5173

### Build for Production

```bash
# Build the app
npm run build

# Preview production build
npm run preview
```

## Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
```

## Usage Flow

1. **Submit Code**: Enter Python code in the Monaco editor
2. **Configure**: Set number of questions and generation strategy
3. **Answer Questions**: Work through generated questions
4. **Get Feedback**: Receive instant feedback on each answer
5. **View Results**: See comprehensive performance summary

## API Integration

The frontend communicates with the backend API through:

- `POST /api/submit-code` - Submit code and get questions
- `POST /api/submit-answer` - Submit answers and get feedback
- `GET /api/health` - Health check
- `GET /api/templates` - Get available question templates

## Component Details

### CodeEditor
Monaco-based Python code editor with syntax highlighting and error detection.

### QuestionDisplay
Displays questions with badges for level (atom/block/relational/macro) and type.

### AnswerInput
Dynamic input component supporting multiple question types:
- Multiple choice
- True/False
- Numeric
- Short answer
- Fill in the blank
- Code selection

### FeedbackDisplay
Shows correctness, score, feedback message, and correct answer (if incorrect).

## Development

```bash
# Run development server with hot reload
npm run dev

# Type checking
npm run build

# Lint code
npm run lint
```

## License

Part of the Final Year Project
