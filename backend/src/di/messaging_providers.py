from collections.abc import AsyncIterator

import aio_pika
from aio_pika.abc import (
    AbstractRobustChannel,
    AbstractRobustConnection,
    AbstractExchange,
)
from dishka import Provider, Scope, provide

from backend.src.settings import RabbitMQSettings
from backend.src.messaging.abstractions import AbstractEventBus
from backend.src.messaging.rabbitmq.event_bus import RabbitMQEventBus


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
