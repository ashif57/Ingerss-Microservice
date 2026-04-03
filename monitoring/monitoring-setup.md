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

---

## 📊 What Data is Being Collected?

Thanks to automatic instrumentation algorithms in OpenTelemetry, you do not need to write custom tracing code. The following telemetry data is collected out-of-the-box:

### 1. Metrics (Prometheus)
Backend services auto-export important health and traffic metrics:
- **HTTP Server Metrics**: `http.server.duration` (latency), `http.server.request.size`, `http.server.response.size`, and `http.server.active_requests`. 
- **HTTP Client Metrics**: `http.client.duration` (time taken calling other microservices like FastAPI calling Node.js).
- **System Metrics**: Out-of-the-box Node.js/Python memory usage, CPU usage, and garbage collection metrics.

### 2. Traces (Jaeger)
Every request generates a distributed trace:
- **Server Spans**: Captures the entry point of the HTTP request into FastAPI/Node.js, including headers, route, method, status code, and execution time.
- **Client Spans**: Outbound network requests (`requests` library in Python) generate spans bridging the two services.
- **Distributed Context**: Trace IDs propagate automatically across service boundaries so you can view the entire flow (`Client -> FastAPI -> NodeBackend`) in a single continuous waterfall chart.

### 3. Logs (Loki)
Application logs are intercepted and forwarded with trace context:
- Python `logging` module captures exceptions, debug logs, and HTTP request access logs, directly forwarding them to Loki.
- Node.js global logger injections catch uncaught errors and console telemetry.
- **Trace correlation**: All logs contain `trace_id` and `span_id`, meaning if you view an error log in Loki, you can immediately jump to the exact Trace in Jaeger.

---

## 3. Docker Compose Integration
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

---

## 📈 Recommended Grafana Dashboards

When working with OpenTelemetry, it is often best to use **separate, focused dashboards** for deep-dives into Metrics and Logs, and rely on Grafana's built-in **"Explore"** view or Jaeger UI for Tracing. 

However, you can build a unified "Observability Overview" by linking them.

Instead of writing thousands of lines of JSON, the Grafana community maintains perfect, pre-built dashboards for our stack. You can instantly import these into Grafana using their **Dashboard IDs**.

### How to Import a Dashboard
1. Go to Grafana at `http://localhost:3000`
2. Click the **`+`** (Plus) icon in the left menu and select **Import**.
3. Paste the ID from the list below and click **Load**.
4. Select the matching Datasource (e.g., `Prometheus` or `Loki`) and click **Import**.

### The Best Dashboard IDs to Import:

#### 1. OpenTelemetry HTTP/Service Metrics (Prometheus)
- **Dashboard ID:** `17878` or `16407`
- **What it does:** This provides a beautiful layout showing Request Rates (RPS), Error Rates, and Latency/Duration percentiles (p95, p99) based on the standard `http.server.*` OpenTelemetry metrics we are emitting from both FastAPI and Node.js.

#### 2. Advanced Logs Dashboard (Loki)
- **Dashboard ID:** `13639` (Loki Search & Insights)
- **What it does:** Provides a unified search interface equipped with visual graphs showing error log frequency, log volume over time, and raw log streaming directly without needing to write complex LogQL queries.

#### 3. Unified View (Metrics + Logs correlation)
To create an "All-in-One" overview for your screen:
1. Import the Metrics Dashboards above.
2. In Grafana, click `Add Panel` on the Metrics dashboard.
3. Choose `Loki` as the data source and use the LogQL query: `{job="otel-collector"} |= "error"`. 
4. Change the panel type to `Logs`.
5. Now you have a dashboard showing service latency metrics directly above your service error logs!

*(Note: Traces are best visualized using the native Jaeger UI or Grafana's "Explore" tab, as trace waterfalls do not fit natively into standard small dashboard panels).*
