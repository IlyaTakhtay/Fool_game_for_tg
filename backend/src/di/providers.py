from collections.abc import AsyncIterator
from typing import Annotated

import aio_pika
from aio_pika.abc import (
    AbstractRobustChannel,
    AbstractRobustConnection,
    AbstractExchange,
)
from dishka import (
    AsyncContainer,
    FromComponent,
    Provider,
    Scope,
    make_async_container,
    provide,
)
from redis.asyncio import Redis

from backend.src.api.managers.connection_managaer import (
    DistributedConnectionManager,
)
from backend.src.api.managers.game_manager import GameManager
from backend.src.settings import RabbitMQSettings, RedisSettings
from backend.src.messaging.abstractions import AbstractEventBus
from backend.src.messaging.rabbitmq.event_bus import RabbitMQEventBus
from backend.src.storage.repositories.interfaces import IGameRepository
from backend.src.storage.repositories.redis import RedisGameRepository


class Components:
    """Названия компонентов для DI"""

    GAME = "game"
    USER = "user"
    CACHE = "cache"


class RabbitMQProvider(Provider):
    """Предоставляет все зависимости для работы с RabbitMQ."""

    @provide(scope=Scope.APP)
    def get_settings(self) -> RabbitMQSettings:
        return RabbitMQSettings()

    @provide(scope=Scope.APP)
    async def get_connection(
        self, settings: RabbitMQSettings
    ) -> AsyncIterator[AbstractRobustConnection]:
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        async with connection:
            yield connection

    @provide(scope=Scope.APP)
    async def get_channel(
        self, connection: AbstractRobustConnection
    ) -> AsyncIterator[AbstractRobustChannel]:
        async with connection.channel() as channel:
            yield channel

    @provide(scope=Scope.APP)
    async def get_exchange(
        self, channel: AbstractRobustChannel, settings: RabbitMQSettings
    ) -> AbstractExchange:
        """Декларирует exchange один раз при старте приложения."""
        return await channel.declare_exchange(
            name=settings.exchange_name,
            type=aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

    @provide(scope=Scope.APP)
    def get_event_bus(
        self, channel: AbstractRobustChannel, exchange: AbstractExchange
    ) -> AbstractEventBus:
        """Создаёт EventBus с готовыми зависимостями."""
        return RabbitMQEventBus(channel, exchange)


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


class GameProvider(Provider):
    """Предоставляет сервис для управления игровой логикой."""

    @provide(scope=Scope.APP)
    def get_game_service(
        self,
        game_repository: Annotated[IGameRepository, FromComponent(Components.GAME)],
        event_bus: AbstractEventBus,
        redis: Annotated[Redis, FromComponent("")],
    ) -> GameManager:
        return GameManager(game_repository, event_bus, redis)


class WebSocketProvider(Provider):
    """Предоставляет зависимости, связанные с WebSocket."""

    @provide(scope=Scope.APP)
    def get_connection_manager(
        self,
        event_bus: AbstractEventBus,
    ) -> DistributedConnectionManager:
        """Предоставляет синглтон `DistributedConnectionManager` для WebSocket-соединений."""

        return DistributedConnectionManager(event_bus)


def create_container() -> AsyncContainer:
    """Создает и конфигурирует контейнер внедрения зависимостей Dishka."""
    return make_async_container(
        RedisClientProvider(),
        RedisGameRepositoryProvider(),
        RabbitMQProvider(),
        GameProvider(),
        WebSocketProvider(),
    )
