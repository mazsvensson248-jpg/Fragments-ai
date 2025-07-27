# Use official Python base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# System dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg libsm6 libxext6 && \
    apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose the port Flask/Gunicorn will run on
EXPOSE 8000

# Gunicorn command to run the Flask app
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]
