# Payment Data Simulator Dockerfile

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Set Python path
ENV PYTHONPATH=/app

# Default command
CMD ["python", "-m", "src.simulator.main"]

# Labels
LABEL maintainer="payments-ingestion-team"
LABEL description="Payment Data Simulator for testing and development"
LABEL version="1.0.0"

