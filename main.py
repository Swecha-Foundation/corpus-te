#!/usr/bin/env python3
"""
Main entry point for the Telugu Corpus Collections API.
Run with: python main.py or uvicorn main:app
"""

import uvicorn
from app.main import app
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )