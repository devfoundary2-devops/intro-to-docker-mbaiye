import os
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, status
import redis
from redis.exceptions import RedisError
import psycopg2


# Configuration via environment variables with sensible defaults
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

PG_HOST = os.getenv("POSTGRES_HOST", os.getenv("PGHOST", "db"))
PG_PORT = int(os.getenv("POSTGRES_PORT", os.getenv("PGPORT", "5432")))
PG_DB = os.getenv("POSTGRES_DB", os.getenv("PGDATABASE", "demo"))
PG_USER = os.getenv("POSTGRES_USER", os.getenv("PGUSER", "demo"))
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", os.getenv("PGPASSWORD", "password"))


app = FastAPI()
logger = logging.getLogger("app")
logging.basicConfig(level=logging.INFO)

# Lazy Redis client
_redis_client: Optional[redis.Redis] = None

def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,  # return strings instead of bytes
        )
    return _redis_client


def get_pg_conn():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
        connect_timeout=5,
    )


def ensure_kv_table(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS kv (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.commit()


@app.on_event("startup")
def on_startup():
    # Attempt to ping Redis
    try:
        get_redis().ping()
        logger.info("Connected to Redis at %s:%s db=%s", REDIS_HOST, REDIS_PORT, REDIS_DB)
    except Exception as e:
        logger.warning("Redis not ready at startup: %s", e)

    # Ensure a simple table exists in Postgres
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS kv (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                    """
                )
                conn.commit()
        logger.info("Connected to Postgres at %s:%s db=%s", PG_HOST, PG_PORT, PG_DB)
    except Exception as e:
        logger.warning("Postgres not ready at startup: %s", e)


@app.get("/cache/{key}")
def cache_get(key: str):
    try:
        val = get_redis().get(key)
    except RedisError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis error: {e}",
        )

    if val is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Key not found")

    return {"key": key, "value": val}


@app.post("/cache/{key}/{value}")
def cache_set(key: str, value: str):
    try:
        ok = get_redis().set(key, value)
    except RedisError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis error: {e}",
        )

    if not ok:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to set value")

    return {"status": "ok"}


@app.get("/db/health")
def db_health():
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                row = cur.fetchone()
        return {"status": "ok", "result": row[0] if row else None}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Postgres error: {e}",
        )

@app.get("/db/kv/{key}")
def db_kv_get(key: str):
    try:
        with get_pg_conn() as conn:
            ensure_kv_table(conn)
            with conn.cursor() as cur:
                cur.execute("SELECT value FROM kv WHERE key=%s", (key,))
                row = cur.fetchone()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Postgres error: {e}")

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Key not found")

    return {"key": key, "value": row[0]}


@app.post("/db/kv/{key}/{value}")
def db_kv_set(key: str, value: str):
    try:
        with get_pg_conn() as conn:
            ensure_kv_table(conn)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO kv (key, value)
                    VALUES (%s, %s)
                    ON CONFLICT (key)
                    DO UPDATE SET value = EXCLUDED.value
                    """,
                    (key, value),
                )
                conn.commit()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Postgres error: {e}")
@app.get("/")


def root():
    return {"message": "Hello from Bootcamp Day 3"}
