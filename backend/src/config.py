from abc import ABC, abstractmethod
from enum import Enum
from typing import Literal
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Общие настройки приложения"""

    app_name: str = "Game API"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    api_version_prefix: str = "v1"
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    class Config:
        env_file = ".env"
        env_prefix = "APP_"  # Префикс : APP_DEBUG, APP_LOG_LEVEL


class StorageSettings(BaseSettings, ABC):
    """Абстрактные настройки хранилища"""

    @abstractmethod
    def get_connection_string(self) -> str:
        pass


class RedisSettings(BaseSettings):
    """Настройки Redis для кеша и хранилища игр"""

    redis_host: str = "redis"
    redis_port: str = "6379"
    redis_password: str | None = "qwezxc"
    redis_db: int = 0
    redis_max_connections: int = 10
    redis_socket_timeout: int = 5
    redis_decode_responses: bool = False

    @property
    def redis_url(self) -> str:
        """Формируем URL для подключения"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}"
        return f"redis://{self.redis_host}:{self.redis_port}"

    class Config:
        env_file = ".env"
        env_prefix = "REDIS_"  # Префикс: REDIS_URL, REDIS_PASSWORD


class PostgresSettings(StorageSettings):
    """Настройки PostgreSQL"""

    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "postgres"
    postgres_host: str = "db"
    postgres_port: int = 5432

    @property
    def postgres_url(self) -> str:
        """Формируем URL для подключения"""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    def get_connection_string(self) -> str:
        return self.postgres_url

    class Config:
        env_file = ".env"
        env_prefix = "POSTGRES_"


class CorsSettings(BaseSettings):
    """Настройки CORS"""

    allow_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:3001",
    ]

    class Config:
        env_file = ".env"
        env_prefix = "CORS_"


class WebSocketSettings(BaseSettings):
    """Настройки WebSocket"""

    base_url: str = "ws://localhost:8000"

    class Config:
        env_file = ".env"
        env_prefix = "WS_"
