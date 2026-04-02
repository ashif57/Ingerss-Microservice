# Observability and Monitoring Setup Guide

This document captures the implementation details of the monitoring stack added to the `ingress3tier` microservices architecture. It includes Prometheus, Grafana, Loki, OpenTelemetry (OTel), and Jaeger. 

## 🏗 Stack Overview

The observability stack focuses on the **three pillars of observability**:
1. **Traces** (Jaeger via OpenTelemetry)
2. **Metrics** (Prometheus via OpenTelemetry)
3. **Logs** (Loki via OpenTelemetry)

The architecture is centered around the **OpenTelemetry Collector (`otel-collector`)**. Both the FastAPI and Node.js backend services send telemetry data directly to this collector via the OTLP protocol. The collector then acts as a router, distributing the data to the appropriate backends.

### Flow Architecture
- **Apps (Node.js & FastAPI)** -> OTLP (Traces, Metrics, Logs) -> **OTel Collector**
- **OTel Collector** -> Traces -> **Jaeger**
- **OTel Collector** -> Metrics -> **Prometheus**
- **OTel Collector** -> Logs -> **Loki**
- **Grafana** -> Queries Prometheus, Jaeger, and Loki for visualization.

---

## 🛠️ What Was Implemented

### 1. Application Instrumentation (OpenTelemetry)

#### FastAPI Service
- **Dependencies**: Added `opentelemetry-distro`, `opentelemetry-exporter-otlp`, `opentelemetry-instrumentation-fastapi`, `opentelemetry-instrumentation-requests`, and `opentelemetry-instrumentation-logging` to `requirements.txt`.
- **Initialization**: Updated `main.py` to programmatically initialize OpenTelemetry attributes (`TracerProvider` and `LoggerProvider`) and added automatic instrumentation via `FastAPIInstrumentor`, `RequestsInstrumentor`, and `LoggingInstrumentor`.

#### Node.js Service
- **Dependencies**: Installed `@opentelemetry/api`, `@opentelemetry/sdk-node`, `@opentelemetry/auto-instrumentations-node`, `@opentelemetry/exporter-metrics-otlp-http`, `@opentelemetry/exporter-trace-otlp-http`, and `@opentelemetry/exporter-logs-otlp-http`.
- **Initialization**: Created `instrumentation.js` and modified the `Dockerfile` to automatically preload OpenTelemetry (`--require ./instrumentation.js`) before starting the app.

### 2. Infrastructure Configurations (`monitoring/`)
- `otel-collector-config.yaml`: Confiugured receivers (gRPC/HTTP), processors (batch), and exporters (Prometheus, Jaeger, Loki).
- `prometheus.yml`: Configured scraping rules to pull metrics from the `otel-collector`.
- `loki-config.yaml`: Simple, local filesystem deployment configuration for storing log chunks.
- `grafana/provisioning/datasources/datasource.yml`: Automatically sets up Prometheus, Loki, and Jaeger as connections in Grafana so no manual linking is needed.

### 3. Docker Compose Integration
Updated `docker-compose.yml` to include the orchestration for:
- `otel-collector` (Ports: `4317` gRPC, `4318` HTTP, `8889` Prometheus metrics exporter)
- `prometheus` (Port: `9090`)
- `loki` (Port: `3100`)
- `jaeger` (UI Port: `16686`)
- `grafana` (UI Port: `3000`) 
*Note: Configured Grafana to allow anonymous admin access locally for convenience.*

We also enriched `fastapi` and `nodebackend` services with `OTEL_EXPORTER_OTLP_ENDPOINT` pointing to `http://otel-collector:4318`.

### 4. Kubernetes Manifests Readiness
Updated `k8s/nodebackend.yaml` and `k8s/fastapi.yaml` with the `OTEL_EXPORTER_OTLP_ENDPOINT` environments. These are now “OTel Ready” and will push data flawlessly if an OpenTelemetry collector is deployed to your K8s cluster (typically handled via the Kube-Prometheus-Stack or official Helm charts).

---

## 🚀 How to Run and Use It with Docker Compose

To launch the full stack locally with the monitoring services active, simply use standard Docker Compose commands.

### 1. Start the Stack
Because the Dockerfiles were modified with new dependencies, ensure you pass the `--build` flag the first time:

```bash
docker-compose up --build -d
```

### 2. Generate Traffic
To see data, the applications need to generate requests. 
Go to the React Frontend at [http://localhost:5173](http://localhost:5173) and click the buttons to generate API calls between the React app, FastAPI, Node.js, and Redis.

### 3. Access Monitoring Dashboards
Navigate to these endpoints in your browser:

*   **Grafana (Central Dashboard)**: [http://localhost:3000](http://localhost:3000)
    *   **Explore**: Use the left menu -> "Explore" and select your data source using the top left dropdown (Prometheus, Loki, or Jaeger) to run queries.
*   **Jaeger UI (Traces)**: [http://localhost:16686](http://localhost:16686)
    *   Look up trace timelines. Select a service (e.g., `fastapi-service`) and click "Find Traces" to view the waterfall flow of requests traversing through the microservices.
*   **Prometheus (Raw Metrics)**: [http://localhost:9090](http://localhost:9090)
    *   Search for OpenTelemetry metrics like `http_server_duration_milliseconds_count` to visualize service throughput.
