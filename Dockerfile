# Use a multi-stage build to reduce the final image size
FROM python:3.11-slim AS builder
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc libffi-dev && rm -rf /var/lib/apt/lists/*

# Copy only necessary files for dependency installation
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Final runtime image
FROM python:3.11-slim
WORKDIR /app

# Add a non-root user for improved security
RUN useradd -m appuser
USER appuser

# Copy installed dependencies from the builder stage
COPY --from=builder /usr/local /usr/local

# Copy the application code
COPY . /app

CMD ["python", "login_monitor.py"]
