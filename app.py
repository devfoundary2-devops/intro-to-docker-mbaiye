from fastapi import FastAPI
import redis

app = FastAPI()
r = redis.Redis(host="redis", port=6379)


@app.get("/cache/{key}")
def cache_get(key: str):
    val = r.get(key)
    return {"key": key, "value": val}


@app.post("/cache/{key}/{value}")
def cache_set(key: str, value: str):
    r.set(key, value)
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Hello from Bootcamp Day 3"}
