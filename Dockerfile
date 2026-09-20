FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY . .

# Expose default port
EXPOSE 8000

# Start FastAPI Uvicorn Server (mendukung $PORT dari Google Cloud Run / Compute Engine)
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
