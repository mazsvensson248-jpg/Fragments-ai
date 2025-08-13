FROM python:3.10-slim

# Install ffmpeg and fonts for subtitle rendering
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Expose port (Render will override with its PORT variable)
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]
