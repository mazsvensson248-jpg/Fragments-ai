# Use a lightweight Python base image
FROM python:3.10-slim

# Prevent Python from writing .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies: git, ffmpeg, build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ffmpeg \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port (Render expects 8000 by default)
EXPOSE 8000

# Start command (change based on your framework)
# Flask example:
# CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]

# FastAPI example (uncomment if using FastAPI instead of Flask):
# CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app:app", "--bind", "0.0.0.0:8000"]

# Temporary: run main.py directly (good for dev/testing)
CMD ["python", "main.py"]
