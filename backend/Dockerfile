FROM python:3.11-slim

# Install UV
RUN pip install uv

WORKDIR /app

# Copy UV configuration files
COPY pyproject.toml uv.lock ./

# Install dependencies directly to system Python using UV
RUN uv pip install --system .

# Copy source code
COPY . .

# Expose port
EXPOSE 5000

# Start the application directly with system Python
CMD ["python", "app.py"]
