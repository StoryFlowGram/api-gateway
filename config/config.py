from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    BOOK_SERVICE_URL: str = "http://book-service:8000"
    AUTH_SERVICE_URL: str = "http://identity-service:8000"
    READER_SERVICE_URL: str = "http://reader-service:8000"
    LEARNING_SERVICE_URL: str = "http://learning-service:8000"
    TRANSLATION_SERVICE_URL: str = "http://translation-service:8000"
    SEARCH_SERVICE_URL: str = "http://search-service:8000"

    ENABLE_DOCS: bool = False
    PUBLIC_ROUTES: list[str] = [
        "auth/telegram",
        "auth/google",
        "auth/google/client-id",
        "auth/callback/google",
        "auth/refresh",
        "auth/logout",
        "book/cover/*",
    ]

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    INTERNAL_GATEWAY_TOKEN: str | None = None
    VERIFY_TOKEN_VERSION: bool = True
    AUTH_REQUEST_TIMEOUT_SECONDS: float = 3.0

    CORS_ALLOW_ORIGINS: str = "https://storyfluentgram.me,https://www.storyfluentgram.me"

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file_encoding="utf-8",
    )

    @property
    def cors_origins(self) -> list[str]:
        return _parse_csv(self.CORS_ALLOW_ORIGINS)


class Config:
    def __init__(self, env_file: str | None = None):
        self.settings = Settings(_env_file=env_file)


config = Config()


def get_service_url(service_name: str) -> str | None:
    mapping = {
        "auth": config.settings.AUTH_SERVICE_URL,
        "book": config.settings.BOOK_SERVICE_URL,
        "reader": config.settings.READER_SERVICE_URL,
        "learning": config.settings.LEARNING_SERVICE_URL,
        "translation": config.settings.TRANSLATION_SERVICE_URL,
        "search": config.settings.SEARCH_SERVICE_URL,
        "users": config.settings.AUTH_SERVICE_URL,
    }
    return mapping.get(service_name)
