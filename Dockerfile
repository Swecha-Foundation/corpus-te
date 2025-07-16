# Use Python 3.13 slim image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Create a non-root user and group for security
RUN groupadd -r appuser && useradd -r -g appuser -s /sbin/nologin -c "Docker image user" appuser

WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv pip install --no-cache-dir --system \
    fastapi \
    uvicorn[standard] \
    gunicorn \
    sqlmodel \
    psycopg2-binary \
    pydantic-settings \
    alembic \
    minio \
    "python-jose[cryptography]" \
    "passlib[bcrypt]" \
    python-multipart \
    "celery[redis]" \
    redis \
    flower \
    python-dotenv \
    email-validator \
    sqlalchemy \
    requests \
    geoalchemy2 \
    "shapely>=2.1.1" \
    posthog

# Copy the application code
COPY . .

# Make celery scripts executable
RUN chmod +x celery_worker.py celery_beat.py

# Change ownership of the app directory to the non-root user
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Default command to run the application with Gunicorn
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "-w", "4", "-b", "0.0.0.0:8000"]
