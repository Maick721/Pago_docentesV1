from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ajustes de ejecución leídos del entorno y, localmente, de backend/.env.

    Los valores siguientes son predeterminados para desarrollo. Las variables
    de entorno pueden reemplazarlos sin modificar el código fuente.
    """

    app_name: str = "ITQ Conecta API"
    database_url: str = (
        "postgresql+asyncpg://itqconecta:itqconecta_dev@localhost:5432/itqconecta"
    )
    redis_url: str = "redis://localhost:6379/0"
    frontend_origin: str = "http://localhost:4200"
    app_version: str = "1.0.0"
    app_description: str = "Backend para el Sistema ITQ Conecta"
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    model_config = SettingsConfigDict(
        # Ruta del archivo de configuración relativo al directorio desde el que
        # se ejecuta el backend, codificación del archivo y tolerancia a extras.
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Se construye una instancia compartida al importar la aplicación. Los módulos
# la consultan para usar la misma configuración durante toda la ejecución.
settings = Settings()
