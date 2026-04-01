import logging

import httpx
from fastapi import APIRouter, HTTPException, Request, Response

from config.config import get_service_url
from config.security import check_authentication

router = APIRouter()
client = httpx.AsyncClient(timeout=15.0)
TRUSTED_SECURITY_HEADERS = {"x-user-id", "x-user-role", "x-gateway-token"}
logger = logging.getLogger(__name__)


@router.api_route("/api/v1/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def reverse_proxy(service_name: str, path: str, request: Request):
    normalized_path = path.strip("/")
    if normalized_path.startswith("internal/"):
        raise HTTPException(status_code=404, detail="Not found")

    target_url = get_service_url(service_name)
    if not target_url:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

    auth_headers = await check_authentication(request, service_name, path)

    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    headers.pop("connection", None)
    for header_name in list(headers):
        if header_name.lower() in TRUSTED_SECURITY_HEADERS:
            headers.pop(header_name, None)

    if auth_headers:
        headers.update(auth_headers)

    url = f"{target_url}/{path}"
    if request.url.query:
        url += f"?{request.url.query}"

    try:
        body = await request.body()
        upstream_response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
            follow_redirects=True,
        )

        excluded_headers = {"content-encoding", "content-length", "transfer-encoding", "connection", "set-cookie"}
        response_headers = {
            key: value
            for key, value in upstream_response.headers.items()
            if key.lower() not in excluded_headers
        }

        response = Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            headers=response_headers,
        )

        for set_cookie_value in upstream_response.headers.get_list("set-cookie"):
            response.headers.append("set-cookie", set_cookie_value)

        return response
    except httpx.RequestError:
        logger.exception("Upstream request failed for service %s path %s", service_name, path)
        raise HTTPException(status_code=503, detail="Upstream service is unavailable")
