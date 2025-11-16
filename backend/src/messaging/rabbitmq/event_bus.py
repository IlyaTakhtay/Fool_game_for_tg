import logging
from typing import Callable, Tuple
from aio_pika import Message, ExchangeType
from aio_pika.abc import AbstractRobustChannel, AbstractRobustQueue

from backend.src.messaging.abstractions import AbstractEventBus, BaseEvent


logger = logging.getLogger(__name__)


class RabbitMQEventBus(AbstractEventBus):
    async def __init__(self, channel: AbstractRobustChannel, exchange_name: str):
        self.channel = channel
        self.exchange_name = exchange_name
        self._exchange = await self.channel.declare_exchange(
            name=self.exchange_name, type=ExchangeType.TOPIC, durable=True
        )

    async def publish(self, routing_key: str, event: BaseEvent):
        """Публикует готовое к отправке событие."""
        message_body = event.model_dump_json().encode()

        await self._exchange.publish(
            Message(body=message_body, content_type="application/json"),
            routing_key=routing_key,
        )

    async def subscribe_to_game_events(
        self, game_id: str, player_id: str, handler: Callable
    ) -> Tuple[str, AbstractRobustQueue]:
        """
        Создает временную очередь и подписывает ее на два типа событий:
        - Общие события игры (game.{game_id}.*)
        - Персональные события для этого игрока (game.{game_id}.player.{player_id})
        """
        queue = await self.channel.declare_queue(exclusive=True, auto_delete=True)

        general_routing_key = f"game.{game_id}.*"
        await queue.bind(self._exchange, routing_key=general_routing_key)

        personal_routing_key = f"game.{game_id}.player.{player_id}"
        await queue.bind(self._exchange, routing_key=personal_routing_key)

        logger.info(
            f"Очередь {queue.name} подписана на '{general_routing_key}' и '{personal_routing_key}'"
        )

        consumer_tag = await queue.consume(handler)
        return consumer_tag, queue

    async def unsubscribe_from_game_events(
        self, consumer_tag: str, queue: AbstractRobustQueue
    ):
        """Отменяет подписку. Очередь удалится сама благодаря auto_delete."""
        await queue.cancel(consumer_tag)
