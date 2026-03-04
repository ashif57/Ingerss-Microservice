import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import uvicorn
import json
from pydantic import BaseModel
import redis

# Connect to Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
r = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

app = FastAPI()

# Rate limiting configuration
RATE_LIMIT = 5 # max requests
RATE_LIMIT_PERIOD = 60 # per 60 seconds

@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    # Use client IP as the unique identifier for rate limiting
    client_ip = request.client.host
    key = f"rate_limit:{client_ip}"
    
    try:
        # Atomic transaction using Redis Pipeline
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.ttl(key)
        results = pipe.execute()
        
        request_count = results[0]
        ttl = results[1]
        
        # If this is the first request, or TTL is missing unexpectedly, set expiry
        if request_count == 1 or ttl == -1:
            r.expire(key, RATE_LIMIT_PERIOD)
            
        # Block the request if the limit is exceeded
        if request_count > RATE_LIMIT:
            current_ttl = r.ttl(key)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests", 
                    "message": f"Rate limit exceeded. Please try again in {current_ttl} seconds."
                }
            )
    except Exception as e:
        # Fallback: if Redis fails, keep the service alive and allow the request
        print(f"Redis rate limiter exception: {e}")
        
    response = await call_next(request)
    return response

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
        # Check if the cache exists
        cached_response = r.get("node_data_cache")
        if cached_response:
            return {
                "message": "FastAPI successfully retrieved data from Redis cache",
                "node_response": json.loads(cached_response),
                "source": "cache"
            }

        # Call the Node.js service if not from cache
        response = requests.get(f"{NODE_SERVICE_URL}/data")
        response.raise_for_status()
        data = response.json()

        # Save to cache with an expiration (e.g., 10 seconds)
        r.setex("node_data_cache", 10, json.dumps(data))

        return {
            "message": "FastAPI successfully called Node.js",
            "node_response": data,
            "source": "api"
        }
    except Exception as e:
        return {"error": f"Failed to call Node.js service: {str(e)}"}

# ---------------------------------------------------------
# Simple Key-Value DB endpoints
# ---------------------------------------------------------

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
