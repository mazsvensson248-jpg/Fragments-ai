FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Install ffmpeg and clean up apt cache properly
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file first to leverage Docker cache
COPY requirements.txt .

# Upgrade pip to avoid possible outdated version issues
RUN pip install --upgrade pip

# Install dependencies with no cache to keep image small
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app.py .

# Expose port 8000
EXPOSE 8000

# Run the app
CMD ["python", "app.py"]
