from collections.abc import AsyncIterator
from typing import Annotated, Final, Type


import aio_pika
from aio_pika.abc import AbstractRobustChannel, AbstractRobustConnection
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
from backend.src.config import AppSettings, RabbitMQSettings, RedisSettings
from backend.src.messaging.abstractions import AbstractEventBus
from backend.src.messaging.rabbitmq.event_bus import RabbitMQEventBus
from backend.src.messaging.rabbitmq.subscription_manager import SubscriptionManager
from backend.src.storage.repositories.interfaces import IGameRepository
from backend.src.storage.repositories.redis import RedisGameRepository


class Components:
    """Названия компонентов для DI"""

    GAME = "game"
    USER = "user"
    CACHE = "cache"


class RabbitMQProvider(Provider):
    @provide(scope=Scope.APP)
    def get_rabbit_settings(self) -> RabbitMQSettings:
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
    async def get_event_bus(
        self, channel: AbstractRobustChannel, settings: RabbitMQSettings
    ) -> AbstractEventBus:
        return RabbitMQEventBus(channel, settings.exchange_name)


class SubscriptionManagerProvider(Provider):
    @provide(scope=Scope.APP)
    def get_subscription_manager(
        self, channel: AbstractRobustChannel, settings: RabbitMQSettings
    ) -> SubscriptionManager:
        return SubscriptionManager(channel, settings.exchange_name)


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
        """Предоставляет экземпляр `RedisGameRepository`."""
        return RedisGameRepository(client=redis)


class GameProvider(Provider):
    """Предоставляет контроллер свзи между логикой игры и её хранимой сущностью."""

    @provide(scope=Scope.APP)
    def get_game_service(
        self,
        game_repository: Annotated[IGameRepository, FromComponent(Components.GAME)],
        event_bus: AbstractEventBus,
        subscription_manager: SubscriptionManager,
    ) -> GameManager:
        """Предоставляет экземпляр `GameManager`, инкапсулирующий бизнес-логику игры."""
        return GameManager(game_repository, event_bus, subscription_manager)


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
        RedisGameRepositoryProvider(),
        GameProvider(),
        WebSocketProvider(),
        RabbitMQProvider(),
        SubscriptionManagerProvider(),
    )
