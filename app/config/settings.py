from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación"""

    # ig-db-mongo service
    IG_DB_MONGO_URL: str = "http://localhost:8087"

    # Procesamiento
    BATCH_SIZE: int = 10000
    MAX_FILE_SIZE_MB: int = 100

    # API
    API_VERSION: str = "v1"
    API_TITLE: str = "MS Client Bulk Load"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()