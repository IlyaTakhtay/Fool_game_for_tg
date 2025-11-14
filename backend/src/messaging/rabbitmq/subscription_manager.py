import asyncio
import logging
from typing import Callable, Coroutine

from aio_pika import ExchangeType
from aio_pika.abc import AbstractRobustChannel, AbstractRobustQueue

logger = logging.getLogger(__name__)


class SubscriptionManager:
    def __init__(self, channel: AbstractRobustChannel, exchange_name: str):
        self.channel = channel
        self.exchange_name = exchange_name

    def _get_queue_name(self, player_id: str) -> str:
        """Generates a deterministic queue name for a player."""
        return f"player_queue_{player_id}"

    async def create_and_bind_queue(self, player_id: str, game_id: str):
        """
        Creates a durable, persistent queue for a player and binds it to the
        game's event exchange. This queue persists across connections.
        """
        queue_name = self._get_queue_name(player_id)
        logger.info(f"Создание и привязка очереди {queue_name} для игрока {player_id}")

        exchange = await self.channel.declare_exchange(
            name=self.exchange_name, type=ExchangeType.TOPIC, durable=True
        )

        # Declare a durable queue that is not auto-deleted or exclusive.
        queue: AbstractRobustQueue = await self.channel.declare_queue(
            name=queue_name, durable=True, exclusive=False, auto_delete=False
        )

        # Bind the queue to the exchange with a wildcard routing key for the game.
        routing_key = f"game.{game_id}.*"
        await queue.bind(exchange, routing_key=routing_key)
        logger.info(
            f"Очередь {queue_name} привязана к exchange '{self.exchange_name}' с ключом '{routing_key}'"
        )

    async def start_consumer(
        self, player_id: str, message_handler: Callable[[str], Coroutine]
    ) -> str:
        """
        Starts a consumer on a player's existing queue.

        :param player_id: The ID of the player.
        :param message_handler: An async callable to process incoming messages.
        :return: The consumer tag of the subscription.
        """
        queue_name = self._get_queue_name(player_id)
        logger.info(f"Запуск потребителя для очереди {queue_name}")
        queue = await self.channel.get_queue(queue_name)

        # Wrapper to pass the original message body to the handler
        async def _message_wrapper(message):
            async with message.process():
                await message_handler(message.body.decode())

        consumer_tag = await queue.consume(_message_wrapper)
        logger.info(f"Потребитель {consumer_tag} запущен для очереди {queue_name}")
        return consumer_tag

    async def stop_consumer(self, consumer_tag: str):
        """
        Stops a consumer (e.g., on WebSocket disconnect) without deleting the queue.

        :param consumer_tag: The consumer tag to cancel.
        """
        logger.info(f"Остановка потребителя {consumer_tag}")
        try:
            await self.channel.basic_cancel(consumer_tag)
            logger.info(f"Потребитель {consumer_tag} успешно остановлен.")
        except Exception as e:
            logger.warning(f"Не удалось остановить потребителя {consumer_tag}: {e}")

    async def delete_queue(self, player_id: str):
        """
        Deletes a player's queue (e.g., when they explicitly exit a game).

        :param player_id: The ID of the player whose queue should be deleted.
        """
        queue_name = self._get_queue_name(player_id)
        logger.info(f"Удаление очереди {queue_name}")
        try:
            await self.channel.queue_delete(queue_name)
            logger.info(f"Очередь {queue_name} успешно удалена.")
        except Exception as e:
            logger.warning(f"Не удалось удалить очередь {queue_name}: {e}")



