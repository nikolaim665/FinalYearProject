# QLC System Frontend Guide

This guide will help you set up and run the complete QLC (Questions about Learners' Code) system with the new React frontend.

## 🎯 Quick Start

### 1. Start the Backend API

From the project root directory:

```bash
# Activate Python virtual environment
source .venv/bin/activate

# Start the FastAPI backend
python run_api.py
```

The backend API will be available at:
- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### 2. Start the Frontend

In a new terminal, from the project root:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
npm install

# Start the development server
npm run dev
```

The frontend will be available at: **http://localhost:3000**

### 3. Use the Application

1. Open http://localhost:3000 in your browser
2. Write or paste Python code in the Monaco editor
3. (Optional) Configure question generation settings
4. Click "Submit Code & Generate Questions"
5. Answer the generated questions
6. Get immediate feedback on your answers

## 📁 Project Structure

```
FinalYearProject/
├── backend/                    # Python backend (FastAPI)
│   ├── analyzers/             # Code analysis (static & dynamic)
│   ├── question_engine/       # Question generation
│   ├── api/                   # REST API endpoints
│   └── database/              # Database models and CRUD
├── frontend/                  # React frontend (NEW!)
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── CodeEditor.jsx
│   │   │   ├── QuestionPanel.jsx
│   │   │   └── ResultsSummary.jsx
│   │   ├── services/
│   │   │   └── api.js        # API client
│   │   ├── App.jsx           # Main app
│   │   └── index.css         # Tailwind styles
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
└── tests/                     # Backend tests
```

## 🎨 Frontend Features

### Monaco Code Editor
- Full VS Code editor experience
- Python syntax highlighting
- Dark theme
- Line numbers and auto-formatting

### Question Generation Settings
- **Max Questions**: Control how many questions to generate (1-20)
- **Strategy**:
  - `diverse`: Balanced mix of question types
  - `focused`: Concentrated on specific patterns
  - `all`: Generate all applicable questions
  - `adaptive`: Adjust based on code complexity
- **Test Inputs**: Optional JSON array to provide test cases

### Question Types
1. **Multiple Choice** - Select from radio options
2. **True/False** - Binary choice questions
3. **Fill in the Blank** - Text input for code elements
4. **Numeric** - Number input for computational answers
5. **Short Answer** - Text area for explanations
6. **Code Selection** - Select specific code snippets

### Visual Features
- **Progress Indicator**: Visual progress bar showing answered questions
  - Blue: Current question
  - Green: Correct answer
  - Red: Incorrect answer
  - Gray: Unanswered
- **Color-coded Badges**:
  - Question level (Atom, Block, Relational, Macro)
  - Difficulty (Easy, Medium, Hard)
  - Question type
- **Real-time Feedback**: Immediate feedback with explanations

## 🔧 Configuration

### Environment Variables

Frontend (`.env` in `frontend/` directory):
```env
VITE_API_URL=http://localhost:8000
```

Backend: No additional configuration needed for local development.

### CORS

The backend is configured to accept requests from any origin in development mode. For production, update `backend/api/app.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-production-domain.com"],  # Update this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🚀 Building for Production

### Frontend

```bash
cd frontend

# Build for production
npm run build

# The build output will be in frontend/dist/
# Deploy this directory to your static hosting service
```

### Backend

```bash
# Install production dependencies
pip install -r requirements.txt

# Run with Gunicorn (production ASGI server)
pip install gunicorn uvicorn[standard]
gunicorn backend.api.app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🧪 Development

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start dev server with hot reload
npm run dev

# Run linter
npm run lint

# Build for production
npm run build

# Preview production build
npm run preview
```

### Backend Development

```bash
# Activate virtual environment
source .venv/bin/activate

# Run tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=backend --cov-report=html

# Run API in development mode
python run_api.py
```

## 📊 API Endpoints

The frontend integrates with these backend endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/submit-code` | POST | Submit code and generate questions |
| `/api/submit-answer` | POST | Submit answer and get feedback |
| `/api/submission/{id}` | GET | Get submission details |
| `/api/submissions` | GET | List all submissions |
| `/api/templates` | GET | List question templates |

## 🎓 Example Workflow

1. **Write Code**:
```python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
print(f"Factorial of 5 is {result}")
```

2. **Submit**: Click "Submit Code & Generate Questions"

3. **View Analysis**:
   - 1 function detected
   - Recursion: Yes
   - Variables, loops, conditionals counted

4. **Answer Questions**:
   - "Which of the following are recursive functions?"
   - "What is the value of `result` after execution?"
   - "How many times is `factorial` called?"

5. **Get Feedback**:
   - ✓ Correct! The function calls itself recursively.
   - ✗ Incorrect. The correct answer is 120.

## 🐛 Troubleshooting

### Frontend won't start
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### CORS errors
- Ensure backend is running on port 8000
- Check that CORS is enabled in `backend/api/app.py`
- Verify API_BASE_URL in frontend `.env` file

### Questions not generating
- Check backend logs for errors
- Verify code has no syntax errors
- Ensure database is initialized

### API connection errors
- Verify backend is running: http://localhost:8000/docs
- Check network tab in browser DevTools
- Ensure `.env` file exists with correct API URL

## 📱 Browser Compatibility

- ✅ Chrome 90+ (Recommended)
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## 🔐 Security Notes

For production deployment:

1. Update CORS origins in backend
2. Add authentication/authorization
3. Use HTTPS
4. Set proper CSP headers
5. Enable rate limiting
6. Use environment-specific API URLs
7. Sanitize all user inputs (already implemented)

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vite.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Monaco Editor](https://microsoft.github.io/monaco-editor/)

## 🤝 Contributing

See main README.md for contribution guidelines.

## 📄 License

MIT License - See LICENSE file for details.
