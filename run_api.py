#!/usr/bin/env python3
"""
Start the QLC API Server

Runs the FastAPI application with uvicorn.
"""

import uvicorn

if __name__ == "__main__":
    print("=" * 80)
    print("Starting QLC API Server")
    print("=" * 80)
    print("API will be available at: http://localhost:8000")
    print("Interactive docs at: http://localhost:8000/docs")
    print("Alternative docs at: http://localhost:8000/redoc")
    print("=" * 80)
    print()

    uvicorn.run(
        "backend.api.app:app", host="0.0.0.0", port=8000, reload=True, log_level="debug"
    )
