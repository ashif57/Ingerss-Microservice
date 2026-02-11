# Build stage
FROM python:3.9-slim AS builder

WORKDIR /app

COPY requirements.txt .
# Install dependencies to a local directory
RUN pip install --no-cache-dir -r requirements.txt --target=/app/site-packages

# Production stage
FROM gcr.io/distroless/python3-debian12

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /app/site-packages /usr/lib/python3.9/site-packages
COPY . .

# Set python path to include installed dependencies
ENV PYTHONPATH=/usr/lib/python3.9/site-packages

EXPOSE 8000

CMD ["main.py"]
