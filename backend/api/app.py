"""
FastAPI Application

Main FastAPI application for the QLC (Questions about Learners' Code) system.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import time
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from api.routes_db import router  # Use database-enabled routes
from api.models import ErrorResponse
from database import init_db

# Create FastAPI app
app = FastAPI(
    title="QLC API - Questions about Learners' Code",
    description="""
    Automated question generation system for student-written Python code.

    This API analyzes student code submissions and generates contextual questions
    to probe their understanding of their own code.

    ## Features

    * **Code Analysis**: Static and dynamic code analysis
    * **Question Generation**: Automated question generation using templates
    * **Multiple Question Types**: Multiple choice, fill-in-blank, numeric, etc.
    * **Flexible Configuration**: Control question selection and filtering
    * **Answer Checking**: Automated feedback on student answers

    ## Workflow

    1. **Submit Code** (`POST /api/submit-code`) - Submit Python code and get questions
    2. **Get Questions** (`GET /api/submission/{id}`) - Retrieve previous submission
    3. **Submit Answer** (`POST /api/submit-answer`) - Submit answer and get feedback
    4. **List Templates** (`GET /api/templates`) - View available question templates

    ## Based on Research

    This system implements concepts from:
    "Let's Ask Students About Their Programs, Automatically"
    by Lehtinen et al. (2021)
    """,
    version="1.0.0",
    contact={
        "name": "Nicolas Moschenross",
        "email": "your.email@example.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to all responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": str(exc),
            "status_code": 422
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": str(exc),
            "status_code": 500
        }
    )


# Include routers
app.include_router(router, prefix="/api", tags=["API"])


# Root endpoint
@app.get("/", tags=["Root"])
def read_root():
    """
    Root endpoint.

    Returns basic API information and links to documentation.
    """
    return {
        "message": "QLC API - Questions about Learners' Code",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/health",
        "endpoints": {
            "submit_code": "POST /api/submit-code",
            "submit_answer": "POST /api/submit-answer",
            "get_submission": "GET /api/submission/{id}",
            "list_templates": "GET /api/templates"
        }
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print("=" * 80)
    print("QLC API - Questions about Learners' Code")
    print("=" * 80)
    print("API is starting up...")
    print("Initializing database...")
    await init_db()
    print("Database initialized successfully!")
    print("Docs available at: http://localhost:8000/docs")
    print("=" * 80)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print("API is shutting down...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
