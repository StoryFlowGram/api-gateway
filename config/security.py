import jwt
from fastapi import Request, HTTPException, status
from .config import Config

settings = Config(".env").settings

def validate_token(token: str) -> dict:

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен истек"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ошибка при валидации токена"
        )

async def check_authentication(request: Request, service_name: str, path: str) -> dict | None:
    route_key = f"{service_name}/{path}"

    is_public = any(pub_route in route_key for pub_route in settings.PUBLIC_ROUTES)


    if is_public:
        return None 
    
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=" Вы не авторизованы. Токен отсутствует"
        )

    try:
        payload = validate_token(token)
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен"
        )
    
    user_id = payload.get("sub") 
    role = payload.get("role", "user")
    
    if not user_id:
         raise HTTPException(status_code=401, detail="Токен не содержит ID")

    return {
        "X-User-Id": str(user_id),
        "X-User-Role": str(role)
        
    }