import logging
import aio_pika
from typing import Dict
from fastapi import WebSocket, WebSocketDisconnect
from aio_pika.abc import AbstractRobustQueue

from backend.src.messaging.rabbitmq.event_bus import RabbitMQEventBus

logger = logging.getLogger(__name__)


class PlayerConnection:
    """Хранит все даные необходимыые жиненному циклу одного websocket соеднинения."""

    def __init__(
        self, websocket: WebSocket, consumer_tag: str, queue: AbstractRobustQueue
    ):
        self.websocket = websocket
        self.consumer_tag = consumer_tag
        self.queue = queue


class DistributedConnectionManager:
    def __init__(self, event_bus: RabbitMQEventBus):
        self.event_bus = event_bus
        self.connections: Dict[str, PlayerConnection] = {}

    async def connect(self, player_id: str, game_id: str, websocket: WebSocket):
        """Полный цикл подключения и подписки."""
        if player_id in self.connections:
            await self.disconnect(player_id)

        await websocket.accept()

        async def message_handler(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    await websocket.send_text(message.body.decode())
                except WebSocketDisconnect:
                    # Штатная ситуация: сокет умер, пока летело сообщение.
                    # Просто игнорируем, disconnect все почистит.
                    pass

        consumer_tag, queue = await self.event_bus.subscribe_to_game_events(
            game_id=game_id, player_id=player_id, handler=message_handler
        )
        self.connections[player_id] = PlayerConnection(websocket, consumer_tag, queue)
        logger.info(
            f"Игрок {player_id} подключен. Создана временная очередь {queue.name}."
        )

    async def disconnect(self, player_id: str):
        """Полный цикл отключения и очистки ресурсов."""
        if player_id in self.connections:
            await self.event_bus.unsubscribe_from_game_events(
                conn_data.consumer_tag, conn_data.queue
            )
            logger.info(
                f"Отключение игрока {player_id}. Отмена подписки {conn_data.consumer_tag}."
            )
            conn_data = self.connections.pop(player_id)
            try:
                await conn_data.websocket.close()
            except RuntimeError:
                pass
            logger.info(f"Ресурсы для игрока {player_id} полностью очищены.")
