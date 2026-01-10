from pydantic_settings import BaseSettings



class Settings(BaseSettings):
    BOOK_SERVICE_URL: str = "http://book-service:8000"
    AUTH_SERVICE_URL: str = "http://identity-service:8000"
    READER_SERVICE_URL: str = "http://reader-service:8000"
    LEARNING_SERVICE_URL: str = "http://learning-service:8000"
    TRANSLATION_SERVICE_URL: str = "http://translation-service:8000"
    


    PUBLIC_ROUTES: list[str] = [
        "docs",
        "openapi.json",
        "auth/telegram", 
        "auth/google",
        "auth/callback/google",
        "auth/refresh"

    ]
    JWT_SECRET_KEY: str 
    JWT_ALGORITHM: str

    model_config = {
        "extra": "ignore",
        "env_file_encoding": "utf-8",
    }
    

class Config:
    def __init__(self, env_file: str | None = None):
        self.settings = Settings(_env_file=env_file)


config = Config(env_file=".env")

def get_service_url(service_name: str) -> str | None:
    mapping = {
        "auth": config.settings.AUTH_SERVICE_URL,
        "book": config.settings.BOOK_SERVICE_URL,
        "reader": config.settings.READER_SERVICE_URL,
        "learning": config.settings.LEARNING_SERVICE_URL,
        "translation": config.settings.TRANSLATION_SERVICE_URL,
        "users": config.settings.AUTH_SERVICE_URL
        

    }
    return mapping.get(service_name)