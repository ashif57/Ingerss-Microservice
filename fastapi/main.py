import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import uvicorn
import json
from pydantic import BaseModel
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
import logging

resource = Resource.create(attributes={
    ResourceAttributes.SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", "fastapi-service")
})

# Tracing
trace_provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318") + "/v1/traces"))
trace_provider.add_span_processor(processor)
trace.set_tracer_provider(trace_provider)

# Metrics
metric_reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318") + "/v1/metrics"))
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)

# Logging
logger_provider = LoggerProvider(resource=resource)
set_logger_provider(logger_provider)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318") + "/v1/logs")))
handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
logging.getLogger().addHandler(handler)

LoggingInstrumentor().instrument()

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()

# Allow requests from React frontend (local and docker)
origins = [
    os.getenv("FRONTEND_URL", "http://localhost:5173"),
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get Node.js service URL from environment variable, default to localhost for local dev
NODE_SERVICE_URL = os.getenv("NODE_SERVICE_URL", "http://localhost:3001")

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI!"}

@app.get("/data")
def read_data():
    return {
        "service": "FastAPI",
        "data": "This is sample data from the FastAPI service."
    }

@app.get("/call-node")
def call_node():
    try:
        # Call the Node.js service
        response = requests.get(f"{NODE_SERVICE_URL}/data")
        return {
            "message": "FastAPI successfully called Node.js",
            "node_response": response.json()
        }
    except Exception as e:
        return {"error": f"Failed to call Node.js service: {str(e)}"}

# ---------------------------------------------------------
# Simple "Redis-like" DB using File System (Simulates Volume)
# ---------------------------------------------------------

import redis

# Connect to Redis
# Host 'redis' is the service name in Docker/K8s
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
r = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

class Item(BaseModel):
    key: str
    value: str

@app.get("/redis")
def read_kv():
    try:
        keys = r.keys("*")
        data = {k: r.get(k) for k in keys}
        return {"db": data, "info": f"Connected to Redis at {REDIS_HOST}"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/redis")
def write_kv(item: Item):
    try:
        r.set(item.key, item.value)
        return {"message": "Saved to Redis", "key": item.key, "value": item.value}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
