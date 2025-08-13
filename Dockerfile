# Use a lightweight Python base image
FROM python:3.10-slim

# Prevent Python from writing .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System deps: ffmpeg (with drawtext), fonts, and libs torchaudio sometimes expects
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-dejavu-core \
    libsndfile1 \
    build-essential \
    ca-certificates \
    git \
 && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements separately for better caching
COPY requirements.txt .

# Install Python deps.
# Important: install CPU wheels for torch to avoid pulling CUDA and to speed up builds.
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy the rest of the application
COPY . .

# Render provides $PORT; gunicorn must bind to it
EXPOSE 8000

# Use gunicorn in production, increase timeout for Whisper/ffmpeg work
ENV PORT=8000 \
    GUNICORN_CMD_ARGS="--bind 0.0.0.0:${PORT} --workers 1 --threads 8 --timeout 600"

# Start the app
CMD ["gunicorn", "app:app"]
