from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.config import Config
from router import proxy
from router.proxy import client

settings = Config().settings

docs_url = "/docs" if settings.ENABLE_DOCS else None
redoc_url = "/redoc" if settings.ENABLE_DOCS else None
openapi_url = "/openapi.json" if settings.ENABLE_DOCS else None

app = FastAPI(
    title="SFG API Gateway",
    description="Unified API gateway",
    version="1.0.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
)

cors_origins = settings.cors_origins
if not cors_origins:
    raise RuntimeError("CORS_ALLOW_ORIGINS must contain at least one allowed origin")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

app.include_router(proxy.router)


@app.on_event("shutdown")
async def shutdown_event():
    await client.aclose()


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "api-gateway",
        "version": "1.0.0",
    }
