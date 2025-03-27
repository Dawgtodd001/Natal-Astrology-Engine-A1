FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY pyproject.toml uv.lock ./

# Install dependencies using pipx and uv
RUN pip install --no-cache-dir pipx && \
    pipx install uv && \
    export PATH="$PATH:/root/.local/bin" && \
    uv pip install -r <(uv pip compile pyproject.toml)

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV API_BASE_URL=/api
ENV REDIS_URL=redis://redis:6379/0

# Expose port
EXPOSE 5000

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--reuse-port", "--reload", "main:app"]