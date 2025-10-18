pec Task DOCKER-1: Dockerized Quick Start Guide
🎯 Objective
To create a complete Docker setup that allows the entire RAG chatbot application—including its Python environment and dependencies—to run within a container. This eliminates the need for any local installation of Python packages or tools, except for Docker itself.

🔑 Key Components & Rationale
Dockerfile: This is the blueprint for building our application's image. It defines the base OS, copies the code, and installs all dependencies from requirements.txt into the image.

.dockerignore: Similar to .gitignore, this file prevents unnecessary or sensitive files (like .venv, .git, .env, __pycache__) from being copied into the Docker image, keeping it lean and secure.

docker-compose.yml: This file makes it easy to run the application. It defines the service, links the Dockerfile, maps volumes for persistent data (chroma_db and data), and injects our environment variables from the .env file.

✅ Acceptance Criteria
A Dockerfile is created in the project root.

A .dockerignore file is created in the project root.

A docker-compose.yml file is created in the project root.

The user can build and run the application using docker-compose up.

The chatbot is fully interactive within the terminal where Docker Compose is running.

The chroma_db directory persists on the host machine even after the container is stopped.

📝 Detailed Steps
Create the Dockerfile:
In the project's root directory, create a file named Dockerfile with the following content:

Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir makes the image smaller
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container
COPY . .

# Command to run the application
CMD ["python", "main.py"]
Create the .dockerignore file:
In the root directory, create a file named .dockerignore to prevent copying unnecessary files into your image.

.git
.gitignore
.venv
venv
__pycache__
.env
chroma_db/
*.pyc
Create the docker-compose.yml file:
In the root directory, create a file named docker-compose.yml. This file orchestrates how your container will run.

YAML

version: '3.8'

services:
  chatbot:
    build: .
    container_name: rag_chatbot
    # Make the container interactive in the terminal
    stdin_open: true 
    tty: true       
    volumes:
      # Mount the local data directory into the container
      - ./data:/app/data
      # Mount a local directory to persist the vector database
      - ./chroma_db:/app/chroma_db
    # Load environment variables from the .env file
    env_file:
      - .env
Update the README.md:
Add a new section to your README.md file explaining how to run the project with Docker.

Markdown

## 🚀 Running with Docker (Recommended)

This project is fully containerized, so you don't need to install Python or any packages on your host machine.

**Prerequisites:**
-   Docker and Docker Compose installed.

**Instructions:**

1.  **Setup:** Ensure you have your data in the `./data` directory and your credentials in a `.env` file as described above.

2.  **Build the Docker image:**
    ```bash
    docker-compose build
    ```

3.  **Run the application:**
    ```bash
    docker-compose up
    ```

4.  The chatbot will initialize and become interactive in your terminal. To stop the application, press `Ctrl+C`. The vector database will be saved in the `./chroma_db` folder on your machine.
