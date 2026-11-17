# Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    awscli \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python -m pip install --no-cache-dir --upgrade pip

# Install project dependencies
RUN python -m pip install --no-cache-dir -r requirements.txt

# Expose FastAPI port
EXPOSE 8000

# Run application directly
CMD ["python", "app.py"]
