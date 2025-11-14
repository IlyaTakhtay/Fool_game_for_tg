from uuid import uuid4
from abc import ABC, abstractmethod
from enum import Enum
from typing import Literal
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Общие настройки приложения"""

    name: str = "Game API"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    api_version_prefix: str = "v1"
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    worker_id: str = str(uuid4())

    class Config:
        env_file = ".env"
        env_prefix = "APP_"
        extra = "ignore"


class StorageSettings(BaseSettings, ABC):
    """Абстрактные настройки хранилища"""

    @abstractmethod
    def get_connection_string(self) -> str:
        pass


class RedisSettings(BaseSettings):
    """Настройки Redis для кеша и хранилища игр"""

    host: str = "redis"
    port: str = "6379"
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

    class Config:
        env_file = ".env"
        env_prefix = "REDIS_"
        extra = "ignore"


class PostgresSettings(StorageSettings):
    """Настройки PostgreSQL"""

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

    class Config:
        env_file = ".env"
        env_prefix = "POSTGRES_"
        extra = "ignore"


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
        extra = "ignore"


class WebSocketSettings(BaseSettings):
    """Настройки WebSocket"""

    base_url: str = "ws://localhost:8000"

    class Config:
        env_file = ".env"
        env_prefix = "WS_"
        extra = "ignore"


class RabbitMQSettings(StorageSettings):
    "Настройки для брокера сообщений RabbitMQ"

    user: str = "guest"
    password: str = "guest"
    host: str = "rabbitmq"
    port: int = 5672
    exchange_name: str = "socket_events_exchange"

    @property
    def rabbitmq_url(self) -> str:
        """Формируем URL для подключения"""
        return (
            f"amqp://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/"
        )

    def get_connection_string(self) -> str:
        return self.rabbitmq_url

    class Config:
        env_file = ".env"
        env_prefix = "RABBITMQ_"
        extra = "ignore"
