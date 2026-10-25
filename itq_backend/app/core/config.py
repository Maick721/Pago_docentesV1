"""
app/core/config.py
Carga la configuración desde el archivo .env usando pydantic-settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Metadatos de la aplicación
    APP_NAME: str = "ITQ Conecta API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Backend para el Sistema ITQ Conecta - Módulo Core y Graduación"


settings = Settings()
