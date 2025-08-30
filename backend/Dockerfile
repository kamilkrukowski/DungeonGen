FROM python:3.11-slim

# Install UV
RUN pip install uv

WORKDIR /app

# Copy UV configuration files
COPY pyproject.toml uv.lock ./

# Install dependencies using UV
RUN uv sync

# Copy source code
COPY . .

# Expose port
EXPOSE 5000

# Start the application
CMD ["uv", "run", "python", "app.py"]
