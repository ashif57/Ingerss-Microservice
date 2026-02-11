# Microservices Communication Demo

A complete 3-tier microservices architecture demonstrating communication flows in **Docker Compose** and **Kubernetes**.

## 🏗 Architecture Overview

The system consists of 4 components:

1.  **frontend (React)**: User Interface.
2.  **fastapi (Python)**: Middleware/Backend service.
3.  **nodebackend (Node.js)**: Internal backend service.
4.  **redis**: Database for storing Key-Value pairs.

### Communication Flows

We demonstrate 3 types of communication:

1.  **Direct Browser to Service**:
    - `Browser` &rarr; `Node.js`
    - `Browser` &rarr; `FastAPI`
2.  **Service to Service (Synchronous)**:
    - `Browser` &rarr; `FastAPI` &rarr; `Node.js`
3.  **Service to Database**:
    - `Browser` &rarr; `FastAPI` &rarr; `Redis`

---

## 🐳 Docker Compose Flow

When running with `docker-compose up`, services run on a shared network.

| Component   | Host Port | Internal Docker URL       | Description                            |
| :---------- | :-------- | :------------------------ | :------------------------------------- |
| **React**   | `5173`    | `http://localhost:5173`   | Access via Browser                     |
| **FastAPI** | `8000`    | `http://fastapi:8000`     | Accessible by React & other containers |
| **Node.js** | `3001`    | `http://nodebackend:3001` | Accessible by React & FastAPI          |
| **Redis**   | `6379`    | `redis:6379`              | Accessible by FastAPI                  |

### Key Flow Details

1.  **React &rarr; FastAPI**: Browser calls `http://localhost:8000` (Mapped Port).
2.  **FastAPI &rarr; Node.js**: FastAPI container calls `http://nodebackend:3001` (Docker DNS).
3.  **FastAPI &rarr; Redis**: FastAPI container calls `redis:6379` (Docker DNS).

---

## ☸️ Kubernetes (K8s) Flow

In Kubernetes, we use an **Ingress Controller** to route traffic. We do NOT expose Node.js or FastAPI directly via NodePorts in production-like setups.

### Ingress Routing Rules

| Path             | Service               | Rewrite Target               |
| :--------------- | :-------------------- | :--------------------------- |
| `/`              | `react-service`       | `/`                          |
| `/api/fastapi/*` | `fastapi-service`     | Remove `/api/fastapi` prefix |
| `/api/node/*`    | `nodebackend-service` | Remove `/api/node` prefix    |

### Key Flow Details

1.  **Browser Request**: User visits `http://localhost` (Ingress Controller).
2.  **Frontend**: Ingress routes direct traffic to React Pods.
3.  **API Calls**:
    - React requests `/api/fastapi/data` &rarr; Ingress &rarr; `fastapi-service` &rarr; `FastAPI Pod`.
    - React requests `/api/node/data` &rarr; Ingress &rarr; `nodebackend-service` &rarr; `Node Pod`.
4.  **Internal Cluster Traffic**:
    - FastAPI calls Node.js: `http://nodebackend-service:3001` (K8s DNS).
    - FastAPI calls Redis: `redis-service:6379` (K8s DNS).

---

## 🚀 How to Run

### Option 1: Docker Compose (Local Dev)

Best for quick testing and development.

```bash
docker-compose up --build
```

- Access App: [http://localhost:5173](http://localhost:5173)

### Option 2: Kubernetes (Production Simulation)

Best for understanding reliable deployment and ingress.

1.  **Build Images**:

    ```bash
    # If using Minikube
    eval $(minikube docker-env)

    # Build all
    docker build -t nodebackend:latest ./nodebackend
    docker build -t fastapi:latest ./fastapi
    docker build -t react:latest ./react
    ```

    _(If using Kind, remember to `kind load docker-image`)_

2.  **Deploy**:

    ```bash
    kubectl apply -f k8s/
    ```

3.  **Access App**:
    - Open [http://localhost](http://localhost) (Uses Ingress Port 80)

---

## 🧪 Testing the Endpoints

Once the UI is running, use these buttons:

1.  **Call Node Service**:
    - Docker: Calls `localhost:3001`
    - K8s: Calls `localhost/api/node`
2.  **Call FastAPI Service**:
    - Docker: Calls `localhost:8000`
    - K8s: Calls `localhost/api/fastapi`
3.  **Call FastAPI &rarr; Node**:
    - Demonstrates **Service Discovery**.
    - FastAPI internally asks DNS for "nodebackend" and gets the IP.
4.  **Redis Test (API Only)**:
    - `POST /redis` to save data.
    - `GET /redis` to read data.
