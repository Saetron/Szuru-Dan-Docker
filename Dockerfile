# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables to prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install git in case dependencies or setup require it
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency list first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose port 9000 (default port specified in config)
EXPOSE 9000

# Command to run the Flask application
CMD ["python", "app.py"]