# Railway.com optimized Dockerfile
FROM python:3.11-slim

# Railway environment setup
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=main.py
ENV FLASK_ENV=production
ENV RAILWAY_ENVIRONMENT=production

# Set Railway-specific working directory
WORKDIR /app

# Install Railway-required system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements for Railway caching
COPY requirements.txt .

# Install Python dependencies with Railway optimizations
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy Railway application code
COPY . .

# Create Railway-required directories
RUN mkdir -p templates static /tmp/fragments_temp /tmp/fragments_output

# Railway port exposure
EXPOSE 8080

# Railway health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Railway-optimized startup
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "300", "--worker-class", "sync", "--max-requests", "50", "--preload", "main:app"]
