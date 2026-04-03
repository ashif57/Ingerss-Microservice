# AWS Deployment Guide for Monitoring Stack (EC2 & ECS)

This document provides a detailed guide on how to deploy the OpenTelemetry (OTel), Prometheus, Grafana, Loki, and Jaeger monitoring stack on AWS, specifically targeting EC2 with Auto Scaling Groups (ASG) and Amazon Elastic Container Service (ECS).

## 🏗 AWS Architecture Overview

When moving from local Docker Compose to AWS production, you have a few architectural choices. The most robust approach is to decouple your application from the monitoring backend.

**Recommended Architecture:**
1. **Application Layer (EC2/ECS)**: Your apps run here with an OpenTelemetry Collector deployed alongside them (either as a Daemonset/Sidecar or a central collector per VPC).
2. **Monitoring Backend Layer (EC2/Managed Services)**: The core monitoring tools (Prometheus, Grafana, Loki, Jaeger) run on a dedicated EC2 instance or ECS cluster, or you utilize AWS Managed Services (AMP, AMG).

---

## 1. Deploying on EC2 with Auto Scaling Groups (ASG)

When deploying applications on EC2 instances managed by an Auto Scaling Group, instances are ephemeral. Long-term storage of metrics and logs on the instances themselves is impossible.

### The Strategy: OTel Collector as an Agent

1.  **Central Monitoring Hub**: Set up a dedicated EC2 instance(s) outside the ASG to run your Monitoring Stack (Prometheus, Loki, Jaeger, Grafana). Assign it a static internal IP or an internal Route 53 DNS record (e.g., `monitoring.internal`).
2.  **ASG Instances**: Install the **OpenTelemetry Collector** directly on the Golden AMI or via User Data (Bootstrap script) on every EC2 instance in the ASG.

### Implementation Steps

#### A. Central Monitoring Node (The Hub)
Deploy the `docker-compose.yml` (minus your apps) on a dedicated EC2 instance.
Make sure its Security Group allows inbound traffic from your ASG on ports:
- `4317` / `4318` (OTEL incoming)
- `8889` (Prometheus)
- `3100` (Loki)

#### B. ASG EC2 User Data (Bootstrap)
When the ASG spins up a new instance, it needs to start the OTel Collector to forward data to the Hub.

```bash
#!/bin/bash
# Install Docker and OTel Collector
yum update -y
amazon-linux-extras install docker -y
service docker start
usermod -a -G docker ec2-user

# Create OTel Config
cat <<EOF > /etc/otel-config.yaml
receivers:
  otlp:
    protocols:
      grpc: { endpoint: 0.0.0.0:4317 }
      http: { endpoint: 0.0.0.0:4318 }
exporters:
  otlp/jaeger:
    endpoint: "monitoring.internal:4317" # Point to the Hub
    tls: { insecure: true }
  prometheusremotewrite:
    endpoint: "http://monitoring.internal:9090/api/v1/write"
  loki:
    endpoint: "http://monitoring.internal:3100/loki/api/v1/push"
service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [otlp/jaeger]
    metrics:
      receivers: [otlp]
      exporters: [prometheusremotewrite]
    logs:
      receivers: [otlp]
      exporters: [loki]
EOF

# Run the Collector
docker run -d --name otel-collector \
  --net=host \
  -v /etc/otel-config.yaml:/etc/otelcol-contrib/config.yaml \
  otel/opentelemetry-collector-contrib:0.91.0 \
  --config=/etc/otelcol-contrib/config.yaml

# Run your Application (e.g. Node Backend)
docker run -d --name my-app \
  --net=host \
  -e OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 \
  -e OTEL_SERVICE_NAME=my-node-app \
  my-registry/nodebackend:latest
```

---

## 2. Deploying on Amazon ECS (Fargate or EC2)

In Amazon ECS, you use the "Sidecar" pattern. The OpenTelemetry Collector runs in the exact same Task Definition as your application container.

### The Strategy: ECS Sidecar Pattern

1.  **Central Monitoring Hub**: Like before, set up your core monitoring stack (Prometheus, Grafana, Loki) on a dedicated EC2 instance or as a separate ECS Service with an internal Load Balancer/Cloud Map namespace.
2.  **ECS Task Definition**: Update your app's task definition to include `aws-otel-collector` (AWS Distro for OpenTelemetry - ADOT) or the standard collector as a second container.

### Implementation Steps

#### ECS Task Definition JSON Extract

In your Task Definition, define two containers: Your app, and the OTel collector. Since they are in the same task, they share the `localhost` network.

```json
{
  "family": "my-app-task",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "my-backend-app",
      "image": "my-registry/nodebackend:latest",
      "portMappings": [{ "containerPort": 3001 }],
      "environment": [
        { "name": "OTEL_EXPORTER_OTLP_ENDPOINT", "value": "http://localhost:4318" },
        { "name": "OTEL_SERVICE_NAME", "value": "ecs-node-app" }
      ]
    },
    {
      "name": "aws-otel-collector",
      "image": "public.ecr.aws/aws-observability/aws-otel-collector:latest",
      "command": [
        "--config=/etc/ecs/ecs-default-config.yaml"
      ],
      "environment": [
        { "name": "JAEGER_ENDPOINT", "value": "monitoring.internal:4317" },
        { "name": "PROMETHEUS_ENDPOINT", "value": "http://monitoring.internal:9090/api/v1/write" },
        { "name": "LOKI_ENDPOINT", "value": "http://monitoring.internal:3100/loki/api/v1/push" }
      ],
      "portMappings": [
        { "containerPort": 4317 },
        { "containerPort": 4318 }
      ],
      "secrets": [
        {
          "name": "AOT_CONFIG_CONTENT",
          "valueFrom": "arn:aws:ssm:region:account-id:parameter/MyOTelConfig"
        }
      ]
    }
  ]
}
```

*Note: You would store a customized `otel-collector-config.yaml` as an AWS Systems Manager (SSM) Parameter and mount it into the ADOT collector to forward telemetry to your central Hub.*

---

## 3. Deploying on Amazon EKS (Kubernetes) using Helm

When deploying to Amazon EKS, the industry-standard approach is to deploy the OpenTelemetry Collector using the official Helm charts, often running it as a DaemonSet so it sits on every EKS worker node. This ensures any Pod on that node can simply send metrics to its local collector (`HostIP`).

You can pair this with the `kube-prometheus-stack` Helm chart for your Grafana and Prometheus monitoring backend.

### The Strategy: DaemonSet + Kube-Prometheus-Stack

1.  **Prometheus & Grafana Backend**: Install the kube-prometheus-stack to handle metrics, alerts, and dashboards.
2.  **OpenTelemetry DaemonSet**: Install the OTel Collector as a DaemonSet to receive OTLP traces, metrics, and logs from your Pods, and forward them to Prometheus, Loki, and Jaeger.

### Implementation Steps

#### A. Install the Core Monitoring Backend (Prometheus + Grafana)
Add the prometheus-community helm repo and install:
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set grafana.enabled=true
```

#### B. Install OpenTelemetry Collector via Helm
Add the OpenTelemetry helm repo and create a `otel-values.yaml` file:
```bash
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update
```

```yaml
# otel-values.yaml
mode: daemonset

config:
  receivers:
    otlp:
      protocols:
        grpc: { endpoint: 0.0.0.0:4317 }
        http: { endpoint: 0.0.0.0:4318 }
  exporters:
    prometheus:
      endpoint: "0.0.0.0:8889"
    # jaeger and loki exporters can be added here
  service:
    pipelines:
      metrics:
        receivers: [otlp]
        exporters: [prometheus]
```

Deploy the collector:
```bash
helm install otel-collector open-telemetry/opentelemetry-collector \
  --namespace monitoring \
  --values otel-values.yaml
```

#### C. Configuring your App Pods
Update your application deployment manifests to send OpenTelemetry data to the *local worker node's IP* where the DaemonSet is listening. You can do this dynamically using the K8S Downward API:

```yaml
env:
  - name: HOST_IP
    valueFrom:
      fieldRef:
        fieldPath: status.hostIP
  - name: OTEL_EXPORTER_OTLP_ENDPOINT
    value: "http://$(HOST_IP):4318"
```

---

## 4. Best Practice: Consider AWS Managed Services

Maintaining a self-hosted Prometheus/Loki/Grafana hub can be complex in production, especially managing storage and scaling. Consider replacing the "Hub" with AWS managed equivalents:

1.  **Traces**: Forward traces from your OTel Collector directly to **AWS X-Ray**.
2.  **Metrics**: Export metrics from OTel directly to **Amazon Managed Service for Prometheus (AMP)**.
3.  **Logs**: Forward logs to **Amazon CloudWatch Logs**.
4.  **Dashboards**: Hook them all up in **Amazon Managed Grafana (AMG)**.

This approach requires ZERO infrastructure management for the monitoring backend. Your EC2 ASG Instances or ECS Tasks simply point their local OTel Collector toward AWS X-Ray, AMP, and CloudWatch.
