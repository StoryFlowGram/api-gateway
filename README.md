# API Gateway

> A single entry point for internal services. It routes requests, validates access tokens, and forwards authenticated context to downstream services.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Running the Service](#running-the-service)
- [Environment Variables](#environment-variables)
- [API](#api)
- [Project Structure](#project-structure)

---

## Overview

This API Gateway is a reverse-proxy built with FastAPI and HTTPX. It accepts incoming HTTP requests from clients, validates tokens from cookies or headers, adds gateway context headers, and forwards each request to the appropriate downstream service.

**Main responsibilities:**
- Token-based authentication
- CORS handling
- Routing by service name under a shared API prefix
- Blocking access to internal paths from external clients

---

## Architecture

```
Client
  │
  ▼
┌─────────────────────┐
│   API Gateway       │  ← FastAPI + HTTPX reverse-proxy
│  /api/v1/{service}/ │
└──────────┬──────────┘
           │ forwards requests
    ┌──────┼──────┐
    ▼      ▼      ▼
  service  service  service
```

---

## Technology Stack

| Package | Version | Role |
|--------|---------|------|
| `fastapi[all]` | ^0.121.1 | Web framework |
| `httpx` | ^0.28.1 | Async HTTP client for proxying |
| `pyjwt` | ^2.10.1 | JWT validation |
| Python | ≥ 3.12 | Runtime |

---

## Running the Service

### Locally (Poetry)

```bash
cd Backend/api-gateway
poetry install
uvicorn main:app --reload --port 8000
```

### Docker

```bash
docker build -t api-gateway .
docker run -p 8000:8000 --env-file .env api-gateway
```

## API

### `GET /health`

Checks whether the gateway is running.

```json
{
  "status": "ok",
  "service": "api-gateway",
  "version": "1.0.0"
}
```

### `* /api/v1/{service_name}/{path}`

Proxies requests to the corresponding downstream service. Supported methods: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`.

> ⚠️ Paths beginning with `/internal/` are not accessible from outside and return `404`.

---

## Project Structure

```
api-gateway/
├── main.py           # Application entry point and FastAPI/CORS setup
├── config/
│   ├── config.py     # Service settings loaded from environment variables
│   └── security.py   # JWT validation logic
├── router/
│   └── proxy.py      # Main reverse-proxy router
├── Dockerfile
└── pyproject.toml
```
