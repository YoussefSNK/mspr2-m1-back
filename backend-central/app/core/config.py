from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    BACKEND_BRESIL_URL: str = "http://backend-bresil:8000"
    BACKEND_EQUATEUR_URL: str = "http://backend-equateur:8000"
    BACKEND_COLOMBIE_URL: str = "http://backend-colombie:8000"

    CORS_ORIGINS: list[str] = ["*"]

    HTTP_TIMEOUT: float = 5.0


def get_settings() -> Settings:
    return Settings()
