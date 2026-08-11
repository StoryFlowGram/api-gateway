import logging

import httpx
import jwt
from fastapi import HTTPException, Request, status

from .config import Config

settings = Config().settings
logger = logging.getLogger(__name__)

DOC_PUBLIC_ROUTES = {"docs", "openapi.json"}


def is_public_route(service_name: str, path: str) -> bool:
    normalized_path = path.strip("/")
    route_key = f"{service_name}/{normalized_path}" if normalized_path else service_name

    for public_route in settings.PUBLIC_ROUTES:
        normalized_public_route = public_route.strip("/")
        if not normalized_public_route:
            continue

        if normalized_public_route.endswith("/*"):
            prefix = normalized_public_route[:-2].strip("/")
            if route_key == prefix or route_key.startswith(f"{prefix}/"):
                return True
            continue

        if route_key == normalized_public_route:
            return True

    if settings.ENABLE_DOCS and normalized_path in DOC_PUBLIC_ROUTES:
        return True

    return False


def validate_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    except Exception:
        logger.exception("Unexpected JWT validation error")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed",
        )


async def _fetch_token_version_from_identity(user_id: int) -> int:
    if not settings.INTERNAL_GATEWAY_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="INTERNAL_GATEWAY_TOKEN is not configured",
        )

    url = f"{settings.AUTH_SERVICE_URL}/internal/users/{user_id}/token-version"
    headers = {"X-Gateway-Token": settings.INTERNAL_GATEWAY_TOKEN}
    timeout = settings.AUTH_REQUEST_TIMEOUT_SECONDS

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url, headers=headers)
    except httpx.RequestError:
        logger.exception("Identity service request failed while validating token version")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to verify token state",
        )

    if resp.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User from token does not exist",
        )

    if resp.status_code != status.HTTP_200_OK:
        logger.error("Unexpected identity response %s: %s", resp.status_code, resp.text)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to verify token state",
        )

    token_version = resp.json().get("token_version")
    if token_version is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Identity did not return token version",
        )

    try:
        return int(token_version)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Identity returned malformed token version",
        )


async def check_authentication(request: Request, service_name: str, path: str) -> dict | None:
    if is_public_route(service_name, path):
        if not settings.INTERNAL_GATEWAY_TOKEN:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="INTERNAL_GATEWAY_TOKEN is not configured",
            )

        return {"X-Gateway-Token": settings.INTERNAL_GATEWAY_TOKEN}

    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not authenticated",
        )

    payload = validate_token(token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Only access tokens can be used for API requests",
        )

    user_id_raw = payload.get("sub")
    if user_id_raw is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token does not contain user ID",
        )

    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token subject",
        )

    if settings.VERIFY_TOKEN_VERSION:
        token_version_claim = payload.get("token_version")
        if token_version_claim is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token does not contain token_version",
            )

        try:
            token_version_claim = int(token_version_claim)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed token_version",
            )

        current_version = await _fetch_token_version_from_identity(user_id)
        if token_version_claim != current_version:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked. Please re-authenticate.",
            )

    role = payload.get("role", "user")
    headers = {
        "X-User-Id": str(user_id),
        "X-User-Role": str(role),
    }

    if not settings.INTERNAL_GATEWAY_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="INTERNAL_GATEWAY_TOKEN is not configured",
        )

    headers["X-Gateway-Token"] = settings.INTERNAL_GATEWAY_TOKEN
    return headers
