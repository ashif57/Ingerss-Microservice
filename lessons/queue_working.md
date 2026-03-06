# How the Message Queue Works in Our Microservices

In this project, we have implemented **asynchronous microservice communication** using **RabbitMQ** as a Message Broker. Instead of our services waiting for each other to finish tasks synchronously (like direct API calls), they communicate by sending messages to a queue.

This decoupling helps with scalability and reliability.

---

## 🏗️ Architecture Overview

The flow of our background processing system works like this:

```
[User App]
     ↓
[ FastAPI (Producer) ] --(JSON Message)--> [ RabbitMQ (Queue) ] --(JSON Message)--> [ Node.js (Consumer) ]
```

### 1. The Producer: FastAPI

FastAPI acts as the front-facing API. When a user sends a request that triggers a background task, FastAPI creates a message (represented as a JSON payload) and **publishes** it to RabbitMQ on a specific queue named `task_queue`.
FastAPI does **not** wait for the task to finish. It immediately returns a response to the user saying "Message sent".

### 2. The Message Broker: RabbitMQ

RabbitMQ receives the message from FastAPI and safely stores it in memory inside the `task_queue`. It will hold onto this message until a consumer is ready to process it. If the Node.js backend crashes, RabbitMQ will keep the message safe and deliver it when Node.js comes back online.

### 3. The Consumer: Node.js Backend

The Node.js backend has a background worker that constantly connects to RabbitMQ and listens to the `task_queue`. As soon as a message appears in the queue, Node.js pulls it out, processes it (for example, simulating a 2-second background job like sending an email), and then sends an **ACK** (acknowledgement) back to RabbitMQ to say "I'm done, you can delete the message now."

---

## 🛠️ Infrastructure Changes & Kubernetes YAML Details

To make this architecture work in Kubernetes, we had to introduce a new RabbitMQ service and modify our existing services so they know how to communicate with it.

### 1. `k8s/rabbitmq.yaml`

This is completely new. We created this file to tell Kubernetes to spin up RabbitMQ.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rabbitmq-deployment
# ...
    spec:
      containers:
      - name: rabbitmq
        image: rabbitmq:3-management-alpine
        ports:
        - containerPort: 5672  # AMQP protocol port (used by FastAPI and Node.js to send/receive messages)
        - containerPort: 15672 # Management UI port (used to access the web dashboard)
```

- **Deployment**: We pull the `rabbitmq:3-management-alpine` image. It contains both the message broker and a web interface management UI.
- **Service (`rabbitmq-service`)**: We expose it internally over the Kubernetes virtual network. Any pod in the cluster can now reach RabbitMQ by simply pinging `rabbitmq-service`.

### 2. `k8s/fastapi.yaml`

FastAPI needs to know where RabbitMQ lives in the Kubernetes cluster so it knows where to send the messages. We added a new environment variable:

```yaml
env:
  # ...
  - name: RABBITMQ_HOST
    value: "rabbitmq-service" # Tells FastAPI to resolve this DNS name inside K8s
```

Because of Kubernetes Internal DNS, `rabbitmq-service` will magically resolve to the IP address of our RabbitMQ pod. The Python `pika` library will use this to connect.

### 3. `k8s/nodebackend.yaml`

Similarly, Node.js needs to know where to connect so it can listen for incoming messages. We injected the same environment variable:

```yaml
env:
  - name: PORT
    value: "3001"
  - name: RABBITMQ_HOST
    value: "rabbitmq-service" # Node.js amqplib connects to amqp://rabbitmq-service
```

Node.js uses the `amqplib` library to establish a long-running WebSocket-like persistent connection to `amqp://rabbitmq-service` on startup.

---

## 🐳 Docker Compose Details

We also updated the `docker-compose.yml` file to reflect these same relationships for local testing.

1. Added a `rabbitmq` block that exposes ports `5672` and `15672` to your localhost.
2. In the `fastapi` and `nodebackend` blocks, we added:
   ```yaml
   environment:
     - RABBITMQ_HOST=rabbitmq
   depends_on:
     - rabbitmq
   ```
   _Docker compose uses internal DNS similarly to Kubernetes, so the containers simply reach out to `rabbitmq`._

---

## 🧪 How to View it in Action

1. **Deploy your changes** (Docker or K8s).
2. Look at the logs for your Node.js container. You should see:
   `Node.js service connected to RabbitMQ. Waiting for messages in task_queue...`
3. Hit the FastAPI `/publish` endpoint with some data:
   ```bash
   curl -X POST http://localhost:8000/publish \
        -H "Content-Type: application/json" \
        -d '{"key": "test_job", "value": "hello from queue!"}'
   ```
4. Look back at the Node.js logs. Almost instantly, you will see output like this:
   ```
   [Node.js Consumer] Received message: {"key": "test_job", "value": "hello from queue!"}
   [Node.js Consumer] Successfully processed message: {"key": "test_job", "value": "hello from queue!"}
   ```
   This proves that the services are successfully talking to each other completely asynchronously using RabbitMQ!
