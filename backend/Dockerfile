FROM python:3.11-slim

# Install UV
RUN pip install uv

WORKDIR /app

# Copy UV configuration files
COPY pyproject.toml uv.lock ./

# Install dependencies using UV and create virtual environment
RUN uv sync --frozen

# Copy source code
COPY . .

# Expose port
EXPOSE 5000

# Start the application using the virtual environment Python
CMD ["uv", "run", "--python", "python", "app.py"]
