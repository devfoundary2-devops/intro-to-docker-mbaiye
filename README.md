[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/q10YQZa2)
[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=20428080&assignment_repo_type=AssignmentRepo)
# Introduction to Docker Assignment

For this assignment, you have a broken `app.py` file. You have to carry out the following to fix the file and application:
- Ensure the `redis` initialization works properly.
- Add error checks to the redis get and set endpoints in your app
- Use the postgres database in your application
- Ensure that a `docker compose up -d` run spins up:
  - The fastapi app
  - The redis cache
  - The postgres db.

You are free to use whatever resources available to you in solving this
task. All that is required is a fully functional docker compose application.

---

## Implementation Summary

This codebase has been updated to provide a fully working FastAPI application with Redis and Postgres, orchestrated via Docker Compose.

Key changes:
- Redis
  - Robust initialization using environment variables (REDIS_HOST, REDIS_PORT, REDIS_DB)
  - Error handling for GET/SET operations on cache endpoints
- Postgres
  - Integrated via psycopg2 with env-driven configuration (POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
  - Startup hook creates a simple kv table
  - Added endpoints to read/write keys to Postgres
- Docker Compose
  - Three services: app (FastAPI), redis, db (Postgres)
  - Health checks for redis and db
  - Named volume for Postgres data (db_data)
- Dependencies
  - requirements.txt now includes: fastapi, uvicorn, redis, psycopg2-binary

## How to Run

Build and start the stack in detached mode:

```bash
docker compose up -d
```

Check status:

```bash
docker compose ps
```

Stop the stack:

```bash
docker compose down
```

## App Endpoints

- Root
  - GET /
  - Returns: { "message": "Hello from Bootcamp Day 3" }

- Redis-backed endpoints
  - POST /cache/{key}/{value}
  - GET /cache/{key}

- Postgres-backed endpoints
  - GET /db/health — checks DB connectivity (SELECT 1)
  - POST /db/kv/{key}/{value}
  - GET /db/kv/{key}

## Quick Smoke Tests

Once the stack is up:

```bash
# Root (add a newline to keep your prompt on the next line)
curl -s -w '\n' http://localhost:8080/

# Redis set/get
curl -s -X POST http://localhost:8080/cache/hello/world
curl -s http://localhost:8080/cache/hello

# Postgres health and KV
curl -s http://localhost:8080/db/health
curl -s -X POST http://localhost:8080/db/kv/foo/bar
curl -s http://localhost:8080/db/kv/foo
```

## Environment

- App listens on port 8080 (host port 8080)
- Redis exposed on port 6379
- Postgres uses a named volume `db_data` for persistence

If you are using an older Docker Compose installation, `docker-compose up -d` also works.
