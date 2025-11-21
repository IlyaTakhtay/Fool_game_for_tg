from uuid import uuid4
from abc import ABC, abstractmethod
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Общие настройки приложения"""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="APP_", extra="ignore"
    )

    name: str = "Game API"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"
    api_prefix: str = "api"
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    worker_id: str = Field(default_factory=lambda: str(uuid4()))


class JWTSettings(BaseSettings):
    """Настройки JWT"""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="JWT_", extra="ignore"
    )

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_hours: int = 24  # 1 day
    cookie_secure: bool = False  # Установить True для production с HTTPS


class StorageSettings(ABC):
    """Абстрактные настройки хранилища"""

    @abstractmethod
    def get_connection_string(self) -> str:
        pass


class RedisSettings(BaseSettings):
    """Настройки Redis для кеша и хранилища игр"""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="REDIS_", extra="ignore"
    )

    host: str = "redis"
    port: int = 6379
    password: str | None = "qwezxc"
    db: int = 0
    max_connections: int = 10
    socket_timeout: int = 5
    decode_responses: bool = False

    @property
    def redis_url(self) -> str:
        """Формируем URL для подключения"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}"
        return f"redis://{self.host}:{self.port}"


class PostgresSettings(BaseSettings, StorageSettings):
    """Настройки PostgreSQL"""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="POSTGRES_", extra="ignore"
    )

    user: str = "postgres"
    password: str = "postgres"
    db: str = "postgres"
    host: str = "db"
    port: int = 5432

    @property
    def postgres_url(self) -> str:
        """Формируем URL для подключения"""
        return (
            f"postgresql://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.db}"
        )

    def get_connection_string(self) -> str:
        return self.postgres_url


class RabbitMQSettings(StorageSettings):
    "Настройки для брокера сообщений RabbitMQ"

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="RABBITMQ_", extra="ignore"
    )

    user: str = "guest"
    password: str = "guest"
    host: str = "rabbitmq"
    port: int = 5672
    exchange_name: str = "socket_events_exchange"

    @property
    def rabbitmq_url(self) -> str:
        """Формируем URL для подключения"""
        return f"amqp://{self.user}:{self.password}@" f"{self.host}:{self.port}/"

    def get_connection_string(self) -> str:
        return self.rabbitmq_url


class CorsSettings(BaseSettings):
    """Настройки CORS"""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="CORS_", extra="ignore"
    )

    allow_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:3001",
    ]


class WebSocketSettings(BaseSettings):
    """Настройки WebSocket"""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="WS_", extra="ignore")

    base_url: str = "ws://localhost:8000"
