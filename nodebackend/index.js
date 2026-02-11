const express = require("express");
const cors = require("cors");

const app = express();
const PORT = process.env.PORT || 3001;

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

app.listen(PORT, () => {
  console.log(`Node.js server is running on http://localhost:${PORT}`);
});
