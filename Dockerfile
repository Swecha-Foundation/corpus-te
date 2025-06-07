# Stage 1: Install dependencies using uv
FROM python:3.13-slim as builder

# Set environment variables for builder stage
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install uv
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy project definition files
# Ensure pyproject.toml lists gunicorn, uvicorn, redis (python client), celery[redis] as dependencies.
COPY pyproject.toml uv.lock ./

# Install dependencies including the project itself into the system's Python environment.
RUN uv pip install --no-cache-dir --system .

# Stage 2: Final application image
FROM python:3.13-slim

# Set environment variables for the final image
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a non-root user and group for security
RUN groupadd -r appuser && useradd -r -g appuser -s /sbin/nologin -c "Docker image user" appuser

WORKDIR /app

# Copy installed Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
# Copy executables (like gunicorn, celery) installed by uv/pip from the builder stage
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy the application code
# This includes your main.py, app/ directory, alembic/ directory, alembic.ini, etc.
COPY . .

# Change ownership of the app directory to the non-root user
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose the port the app runs on (Gunicorn will bind to this port)
EXPOSE 8000

# Command to run the application with Gunicorn
# The number of workers (-w) can be adjusted based on your VM's CPU cores (e.g., 2 * num_cores + 1)
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "-w", "4", "-b", "0.0.0.0:8000"]
