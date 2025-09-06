# Use Python 3.11 slim image for Lambda compatibility
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install pipenv
RUN pip install pipenv

# Copy Pipfile and Pipfile.lock (if it exists) for dependency installation
COPY Pipfile ./
COPY Pipfile.lock* ./

# Install Python dependencies using pipenv
# Try to use lock file if present, otherwise install from Pipfile
RUN if [ -f Pipfile.lock ]; then \
        pipenv install --system --deploy; \
    else \
        pipenv install --system --skip-lock; \
    fi

# Debug: Check if numpy was installed
RUN python -c "import numpy; print(f'NumPy version: {numpy.__version__}')" || echo "NumPy not available"

# Copy the source code
COPY src/ .

# Set environment variables
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]
