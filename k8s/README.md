# Running the Project on Kubernetes

This folder contains the Kubernetes manifests to deploy the 3-tier application with an Ingress Controller.

## Prerequisites

1.  **Kubernetes Cluster**: Use Docker Desktop (Enable Kubernetes) or Minikube.
2.  **Ingress Controller**: You MUST enable the Nginx Ingress Controller.

## Steps

### 1. Build Docker Images Locally (With Build Args)

⚠️ **Important**: React apps are static. You must bake the API URLs into the image at build time.

**For Docker Desktop:**

```bash
docker build -t nodebackend:latest ./nodebackend
docker build -t fastapi:latest ./fastapi

# React Build with K8s specific URLs (Ingress paths)
docker build \
  --build-arg VITE_NODE_API_URL="http://localhost/api/node" \
  --build-arg VITE_FASTAPI_URL="http://localhost/api/fastapi" \
  -t react:latest ./react
```

**For Minikube:**

```bash
eval $(minikube docker-env)

docker build -t nodebackend:latest ./nodebackend
docker build -t fastapi:latest ./fastapi

# React Build
docker build \
  --build-arg VITE_NODE_API_URL="http://localhost/api/node" \
  --build-arg VITE_FASTAPI_URL="http://localhost/api/fastapi" \
  -t react:latest ./react
```

### 2. Apply Kubernetes Manifests

Apply all files in the `k8s` folder:

```bash
kubectl apply -f k8s/
```

### 3. Verification & Access

1.  Check pods: `kubectl get pods`
2.  Check Ingress: `kubectl get ingress`
3.  Open browser: **http://localhost**
