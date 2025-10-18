# Dockerfile for RAG Chatbot
# This image includes all system dependencies needed for multi-modal processing:
# - ffmpeg: For extracting audio from video files (MP4)
# - poppler-utils: For converting PDF pages to images

# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
# ffmpeg: Required for video processing (extracting audio from MP4 files)
# poppler-utils: Required for PDF to image conversion (pdf2image library dependency)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir reduces the image size by not caching pip packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container
# (Note: .dockerignore will prevent unnecessary files from being copied)
COPY . .

# Command to run the application
# This will start the interactive chatbot CLI
CMD ["python", "main.py"]
