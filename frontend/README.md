# QLC System Frontend

Modern React frontend for the Questions about Learners' Code (QLC) system.

## Features

- **Monaco Code Editor** - VS Code-powered code editor with Python syntax highlighting
- **Real-time Question Generation** - Submit code and get instant comprehension questions
- **Interactive Question Answering** - Multiple question types (multiple choice, fill-in-blank, numeric, etc.)
- **Immediate Feedback** - Get instant feedback on your answers with explanations
- **Analysis Dashboard** - View detailed analysis of your code (functions, variables, loops, etc.)
- **Responsive Design** - Beautiful UI built with Tailwind CSS

## Tech Stack

- **Vite** - Fast build tool and dev server
- **React 19** - Modern React with hooks
- **Tailwind CSS** - Utility-first CSS framework
- **Monaco Editor** - VS Code's editor component
- **Axios** - HTTP client
- **Lucide React** - Beautiful icons

## Getting Started

### Prerequisites

- Node.js 16+
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Building for Production

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── CodeEditor.jsx       # Monaco code editor component
│   │   ├── QuestionPanel.jsx    # Question display and answering
│   │   └── ResultsSummary.jsx   # Analysis results display
│   ├── services/
│   │   └── api.js              # API client
│   ├── App.jsx                 # Main application component
│   ├── index.css               # Global styles with Tailwind
│   └── main.jsx                # Application entry point
├── public/                     # Static assets
├── index.html                  # HTML template
├── vite.config.js             # Vite configuration
├── tailwind.config.js         # Tailwind CSS configuration
└── package.json               # Dependencies and scripts
```

## Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
```

## API Integration

The frontend connects to the FastAPI backend with the following endpoints:

- `GET /health` - Health check
- `POST /submit-code` - Submit code and generate questions
- `POST /submit-answer` - Submit answer to a question
- `GET /submission/{id}` - Get submission details
- `GET /submissions` - List all submissions
- `GET /templates` - List question templates

## Component Overview

### CodeEditor

- Monaco editor for Python code
- Configurable question generation settings
- Code submission with loading states

### QuestionPanel

- Display questions one at a time
- Progress indicator for all questions
- Support for multiple question types
- Immediate feedback on answers
- Navigation between questions

### ResultsSummary

- Display generation metadata
- Show code analysis statistics
- Display errors and warnings

## Development

```bash
# Run in development mode with hot reload
npm run dev

# Run linter
npm run lint

# Build for production
npm run build
```

## Features in Detail

### Question Types Supported

1. **Multiple Choice** - Select from radio button options
2. **True/False** - Binary choice questions
3. **Fill in the Blank** - Text input for missing code elements
4. **Numeric** - Number input for computational questions
5. **Short Answer** - Text area for explanations
6. **Code Selection** - Select code snippets

### Question Levels (Block Model)

- **Atom** - Language elements (variables, values)
- **Block** - Code sections (loops, functions)
- **Relational** - Connections between code parts
- **Macro** - Whole program understanding

### Visual Feedback

- ✓ Green checkmark for correct answers
- ✗ Red cross for incorrect answers
- Progress bar showing answered questions
- Color-coded badges for difficulty and level

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

## License

MIT License - See LICENSE file for details
