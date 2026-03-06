const express = require("express");
const cors = require("cors");
const amqp = require("amqplib");

const app = express();
const PORT = process.env.PORT || 3001;
const RABBITMQ_HOST = process.env.RABBITMQ_HOST || "localhost";
const RABBITMQ_URL = `amqp://${RABBITMQ_HOST}`;
const QUEUE_NAME = "task_queue";

app.use(cors());
app.use(express.json());

app.get("/", (req, res) => {
  res.json({ message: "Hello from Node.js Backend!" });
});

app.get("/data", (req, res) => {
  res.json({
    service: "Node.js",
    timestamp: new Date().toISOString(),
    data: "This is sample data from the Node.js service.",
  });
});

// RabbitMQ initialization and consumer
async function connectRabbitMQ() {
  try {
    console.log(`Attempting to connect to RabbitMQ at ${RABBITMQ_URL}...`);
    const connection = await amqp.connect(RABBITMQ_URL);
    const channel = await connection.createChannel();
    await channel.assertQueue(QUEUE_NAME, { durable: true });

    console.log(
      `Node.js service connected to RabbitMQ. Waiting for messages in ${QUEUE_NAME}...`,
    );

    channel.consume(QUEUE_NAME, (msg) => {
      if (msg !== null) {
        const content = msg.content.toString();
        console.log(`[Node.js Consumer] Received message: ${content}`);

        // Simulate background processing (e.g. sending emails, generating reports)
        setTimeout(() => {
          console.log(
            `[Node.js Consumer] Successfully processed message: ${content}`,
          );
          channel.ack(msg); // acknowledge message after processing
        }, 2000);
      }
    });
  } catch (error) {
    console.error(`Failed to connect to RabbitMQ: ${error.message}`);
    // Retry connection since DB dependencies might take longer to start
    console.log("Retrying RabbitMQ connection in 5 seconds...");
    setTimeout(connectRabbitMQ, 5000);
  }
}

// Start RabbitMQ consumer
connectRabbitMQ();

app.listen(PORT, () => {
  console.log(`Node.js server is running on http://localhost:${PORT}`);
});
