# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container to /app
WORKDIR /app

# Copy the pyproject.toml and other necessary files
COPY pyproject.toml .
COPY src ./src
COPY tests ./tests

# Copy the .env file into the container
COPY .env /app/

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3-pip \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libjpeg-dev \
    libopenjp2-7-dev \
    libffi-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install optional dependencies if needed
RUN pip install --no-cache-dir ".[all]"

# Copy the rest of the application code into the container
COPY . /app

# Make port 80 available to the world outside this container
EXPOSE 8001

# Run the application when the container launches
CMD ["python", "src/real_estate_telegram_bot/main.py"]
