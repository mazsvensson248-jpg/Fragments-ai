# Use a minimal base image with Python
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Ensure output is logged straight to terminal
ENV PYTHONUNBUFFERED=1

# Install system dependencies (for ffmpeg and Whisper)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && apt-get clean

# Copy requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose the port Flask/Gunicorn will run on
EXPOSE 8080

# Start the app with Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]
