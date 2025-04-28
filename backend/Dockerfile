ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/backend

WORKDIR /app

# Copy only what's needed for installing dependencies first
COPY requirements.txt .
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# Install dependencies with cache
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Create non-root user
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Now copy application code
COPY . .

# Create and set permissions for logs directory
RUN mkdir -p logs && \
    chmod 777 logs && \
    chown -R appuser:appuser logs

# Switch to non-root user
USER appuser

EXPOSE 80

ENTRYPOINT ["/wait-for-it.sh", "postgres:5432", "--", "python", "-c", "import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=80, log_level='debug')"]
