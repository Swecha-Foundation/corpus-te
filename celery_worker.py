#!/usr/bin/env python3
"""
Celery Worker entry point for the corpus-te application.
This handles background task processing.
"""
import os
import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from app.core.celery_app import celery_app

if __name__ == "__main__":
    # Start the Celery Worker
    celery_app.start([
        "worker", 
        "--loglevel=info",
        "--queues=default,file_processing,data_analysis,notifications,maintenance",
        "--concurrency=2"
    ])