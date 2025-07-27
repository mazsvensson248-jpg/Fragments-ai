# Use Python base image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy all your app files into the container
COPY . /app

# Install system dependencies (for ffmpeg)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Expose the port your app runs on
EXPOSE 8080

# Run the app with Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
