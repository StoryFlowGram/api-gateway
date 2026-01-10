import httpx
from fastapi import APIRouter, Request, Response, HTTPException
from config.config import get_service_url
from config.security import check_authentication

router = APIRouter()
client = httpx.AsyncClient()

@router.api_route("/api/v1/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def reverse_proxy(service_name: str, path: str, request: Request):
    
    target_url = get_service_url(service_name)
    if not target_url:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

    auth_headers = await check_authentication(request, service_name, path)
    
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None) 
    headers.pop("connection", None)
    
    if auth_headers:
        headers.update(auth_headers)

    url = f"{target_url}/{path}"
    if request.url.query:
        url += f"?{request.url.query}"

    try:
        body = await request.body()
        
        rp_resp = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
            follow_redirects=True
        )

        excluded_headers = {"content-encoding", "content-length", "transfer-encoding", "connection", "set-cookie"}
        
        response_headers = {
            k: v for k, v in rp_resp.headers.items() 
            if k.lower() not in excluded_headers
        }

        response = Response(
            content=rp_resp.content,
            status_code=rp_resp.status_code,
            headers=response_headers
        )

        for cookie in rp_resp.cookies.jar:
            response.set_cookie(
                key=cookie.name,
                value=cookie.value,
                httponly=True,
                secure=True, 
                samesite="none",
                path=cookie.path if cookie.path else "/"
            )

        return response

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {e}")