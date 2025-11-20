from typing import Annotated, AsyncIterator

from dishka import FromComponent, Provider, Scope, provide
from redis.asyncio import Redis

from backend.src.settings import RedisSettings
from backend.src.storage.repositories.interfaces import IGameRepository
from backend.src.storage.repositories.redis import RedisGameRepository
from backend.src.di.components import Components


class RedisClientProvider(Provider):
    """Предоставляет настройки и асинхронный клиент Redis."""

    @provide(scope=Scope.APP)
    def get_redis_settings(self) -> RedisSettings:
        return RedisSettings()

    @provide(scope=Scope.APP)
    async def get_redis_client(self, settings: RedisSettings) -> AsyncIterator[Redis]:
        client = Redis.from_url(
            settings.redis_url,
            password=settings.password,
            decode_responses=settings.decode_responses,
        )
        yield client
        await client.aclose()


class RedisGameRepositoryProvider(Provider):
    """Предоставляет реализацию управления хранением игр в Redis."""

    component = Components.GAME

    @provide(scope=Scope.APP)
    def get_game_repository(
        self, redis: Annotated[Redis, FromComponent("")]
    ) -> IGameRepository:
        return RedisGameRepository(client=redis)
