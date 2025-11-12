from collections.abc import AsyncIterator
from typing import Annotated, Final, Type

from dishka import (
    AsyncContainer,
    FromComponent,
    Provider,
    Scope,
    make_async_container,
    provide,
)
from redis.asyncio import Redis

from backend.src.api.managers.connection_managaer import ConnectionManager
from backend.src.api.managers.game_manager import GameManager
from backend.src.config import AppSettings, RedisSettings
from backend.src.storage.repositories.interfaces import IGameRepository
from backend.src.storage.repositories.redis import RedisGameRepository


class Components:
    """Названия компонентов для DI"""

    GAME = "game"
    USER = "user"
    CACHE = "cache"


class RedisClientProvider(Provider):
    """Предоставляет настройки и асинхронный клиент Redis."""

    @provide(scope=Scope.APP)
    def get_redis_settings(self) -> RedisSettings:
        """Предоставляет настройки подключения к Redis."""
        return RedisSettings()

    @provide(scope=Scope.APP)
    async def get_redis_client(self, settings: RedisSettings) -> AsyncIterator[Redis]:
        """Предоставляет асинхронный клиент Redis, управляя его жизненным циклом."""
        client = Redis.from_url(
            settings.redis_url,
            password=settings.redis_password,
            decode_responses=settings.redis_decode_responses,
        )
        yield client
        await client.aclose()


class GameRepositoryProvider(Provider):
    """Предоставляет реализацию репозитория игр."""

    component = Components.GAME

    @provide(scope=Scope.APP)
    def get_game_repository(self, redis: Redis) -> IGameRepository:
        """Предоставляет экземпляр `RedisGameRepository`."""
        return RedisGameRepository(client=redis)


class GameProvider(Provider):
    """Предоставляет сервисы игрового домена."""

    @provide(scope=Scope.APP)
    def get_game_service(
        self,
        game_repository: Annotated[IGameRepository, FromComponent(Components.GAME)],
    ) -> GameManager:
        """Предоставляет экземпляр `GameManager`, инкапсулирующий бизнес-логику игры."""
        return GameManager(game_repository)


class WebSocketProvider(Provider):
    """Предоставляет зависимости, связанные с WebSocket."""

    @provide(scope=Scope.APP)
    def get_connection_manager(
        self,
    ) -> ConnectionManager:
        """Предоставляет синглтон `ConnectionManager` для WebSocket-соединений."""
        return ConnectionManager()


def create_container() -> AsyncContainer:
    """Создает и конфигурирует контейнер внедрения зависимостей Dishka."""
    return make_async_container(
        RedisClientProvider(),
        GameRepositoryProvider(),
        GameProvider(),
        WebSocketProvider(),
    )
