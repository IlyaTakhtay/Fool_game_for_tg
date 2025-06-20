import logging
from typing import Dict, List, Optional, Union
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Менеджер подключений. Управляет WebSocket соединениями игроков.
    """

    def __init__(self):
        """
        Инициализация менеджера подключений.

        Атрибуты:
            connections (dict): Словарь вида {player_id: websocket},
                              где хранится информация о подключениях игроков.
        """
        self.connections: dict[str, WebSocket] = {}  # {player_id: websocket}

    async def connect(self, player_id: str, websocket: WebSocket):
        """
        Подключает игрока и сохраняет его WebSocket соединение.

        Args:
            player_id (str): Уникальный идентификатор игрока.
            websocket (WebSocket): WebSocket соединение игрока.
        """
        if not player_id:
            raise ValueError("player_id не может быть пустым")

        # Закрываем старое соединение, если оно есть
        if player_id in self.connections:
            old_websocket = self.connections[player_id]
            try:
                await old_websocket.close(code=1000, reason="Reconnection")
            except Exception as e:
                logger.error(
                    f"Ошибка при закрытии старого соединения для игрока {player_id}: {e}"
                )

        # Создаем новое соединение
        try:
            await websocket.accept()
        except Exception as e:
            logger.debug(f"WebSocket уже принят для игрока {player_id}: {e}")

        # Сохраняем соединение
        self.connections[player_id] = websocket
        logger.info(f"Игрок {player_id} подключен")

    def disconnect(self, player_id: str):
        """
        Отключает игрока и удаляет его WebSocket соединение.

        Args:
            player_id (str): Уникальный идентификатор игрока.
        """
        if player_id in self.connections:
            del self.connections[player_id]
            logger.info(f"Игрок {player_id} отключен")

    async def broadcast_to_players(
        self,
        player_ids: List[str],
        message: dict,
        exclude: Union[str, List[str], None] = None,
    ) -> int:
        """
        Отправляет сообщение указанным игрокам.

        Args:
            player_ids (List[str]): Список ID игроков для отправки.
            message (dict): Сообщение для отправки в формате JSON.
            exclude (str | list[str] | None): ID игрока(ов) которых нужно исключить из рассылки.

        Returns:
            int: Количество игроков, которым успешно доставлено сообщение.
        """
        excluded_players = []
        if exclude:
            excluded_players = [exclude] if isinstance(exclude, str) else exclude

        successful_sends = 0
        failed_players = []

        for player_id in player_ids:
            if player_id in excluded_players:
                continue

            if player_id not in self.connections:
                logger.warning(f"Игрок {player_id} не имеет активного соединения")
                continue

            try:
                await self.connections[player_id].send_json(message)
                successful_sends += 1
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения игроку {player_id}: {e}")
                failed_players.append(player_id)

        for player_id in failed_players:
            self.disconnect(player_id)

        if failed_players:
            logger.warning(
                f"Удалены игроки с неработающими соединениями: {failed_players}"
            )

        return successful_sends

    async def send_message(self, player_id: str, message: dict) -> bool:
        """
        Отправляет сообщение одному игроку.

        Args:
            player_id (str): Уникальный идентификатор игрока.
            message (dict): Сообщение для отправки в формате JSON.

        Returns:
            bool: True если сообщение успешно отправлено, False в противном случае.
        """
        if player_id not in self.connections:
            logger.warning(f"Игрок {player_id} не имеет активного соединения")
            return False

        try:
            await self.connections[player_id].send_json(message)
            return True
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения игроку {player_id}: {e}")
            self.disconnect(player_id)
            return False

    def get_connection(self, player_id: str) -> Optional[WebSocket]:
        """
        Возвращает WebSocket соединение игрока.

        Args:
            player_id (str): Уникальный идентификатор игрока.

        Returns:
            Optional[WebSocket]: WebSocket соединение игрока или None, если соединение не найдено.
        """
        return self.connections.get(player_id)

    def is_connected(self, player_id: str) -> bool:
        """
        Проверяет, подключен ли игрок.

        Args:
            player_id (str): Уникальный идентификатор игрока.

        Returns:
            bool: True если игрок подключен, False в противном случае.
        """
        return player_id in self.connections
