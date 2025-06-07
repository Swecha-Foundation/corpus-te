#!/usr/bin/env python3
"""
Celery Beat scheduler entry point for the corpus-te application.
This handles periodic/scheduled tasks.
"""
import os
import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from app.core.celery_app import celery_app

if __name__ == "__main__":
    # Start the Celery Beat scheduler
    celery_app.start(["beat", "--loglevel=info"])
