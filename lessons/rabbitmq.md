# RabbitMQ in FastAPI

We have added a RabbitMQ queuing layer to our FastAPI service. This helps decouple message production from message consumption, making the system more resilient and scalable.

## What is RabbitMQ?

RabbitMQ is an open-source message broker software that implements the Advanced Message Queuing Protocol (AMQP). It accepts, stores, and forwards messages between services.

## Architecture Updates

1. **Docker Compose**: We've added a `rabbitmq:3-management-alpine` container, available on port `5672` (AMQP) and `15672` (Management UI). The FastAPI container is now linked to it via the `RABBITMQ_HOST` environment variable.
2. **Dependencies**: Added `pika` to `fastapi/requirements.txt`, which is a standard library to interact with RabbitMQ in Python.
3. **FastAPI Endpoints**: Modified `fastapi/main.py` with two new endpoints:
   - `POST /publish` - Accepts a JSON body with `key` and `value` and publishes it to the `task_queue` in RabbitMQ.
   - `GET /consume` - Retrieves exactly one message from the `task_queue`.

## Endpoints

### 1. Publish a Message

You can publish a message to the RabbitMQ `task_queue`. This simulates a background job or event payload.

**Request:**

```http
POST /publish
Content-Type: application/json

{
    "key": "order_123",
    "value": "Process order details"
}
```

**Response:**

```json
{
  "message": "Message published to RabbitMQ",
  "data": "{\"key\": \"order_123\", \"value\": \"Process order details\"}"
}
```

### 2. Consume a Message

You can consume messages synchronously. This fetches a single message from the queue and acknowledges it.

**Request:**

```http
GET /consume
```

**Response (if a message exists):**

```json
{
  "message": "Successfully consumed message",
  "data": {
    "key": "order_123",
    "value": "Process order details"
  }
}
```

**Response (if queue is empty):**

```json
{
  "message": "No messages in queue"
}
```

## How to Test

1. Rebuild and start your docker containers:
   ```bash
   docker-compose down
   docker-compose up --build -d
   ```
2. Hit the `/publish` endpoint a few times using `curl` or Postman.
3. Hit the `/consume` endpoint to see the messages being processed one by one.
4. Verify the Management UI at [http://localhost:15672](http://localhost:15672) (Default credentials: `guest` / `guest`).
