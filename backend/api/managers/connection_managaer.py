from collections import defaultdict
from fastapi import WebSocket

class ConnectionManager:
    """
    Менеджер подключений. Управляет WebSocket соединениями игроков и их привязкой к играм.
    """
    def __init__(self):
        """
        Инициализация менеджера подключений.
        
        Атрибуты:
            game_players (defaultdict): Словарь вида {game_id: {player_id: websocket}}, 
                                        где хранится информация о подключениях игроков к играм.
        """
        self.game_players = defaultdict(dict)  # {game_id: {player_id: websocket}}
    
    async def connect(self, game_id: str, player_id: str, websocket: WebSocket):
        """
        Подключает игрока к игре и сохраняет его WebSocket соединение.

        Args:
            game_id (str): Уникальный идентификатор игры.
            player_id (str): Уникальный идентификатор игрока.
            websocket (WebSocket): WebSocket соединение игрока.

        Raises:
            RuntimeError: Если соединение уже существует для данного игрока в игре.
        """
        if player_id in self.game_players[game_id]:
            raise RuntimeError(f"Игрок {player_id} уже подключен к игре {game_id}.")
        
        self.game_players[game_id][player_id] = websocket
    
    def disconnect(self, game_id: str, player_id: str):
        """
        Отключает игрока от игры и удаляет его WebSocket соединение.

        Args:
            game_id (str): Уникальный идентификатор игры.
            player_id (str): Уникальный идентификатор игрока.

        Raises:
            KeyError: Если игрок или игра не найдены.
        """
        if game_id in self.game_players and player_id in self.game_players[game_id]:
            self.game_players[game_id].pop(player_id)
    
    async def broadcast(self, game_id: str, message: dict):
        """
        Отправляет сообщение всем подключенным игрокам в указанной игре.

        Args:
            game_id (str): Уникальный идентификатор игры.
            message (dict): Сообщение для отправки в формате JSON.

        Raises:
            KeyError: Если игра не найдена.
            RuntimeError: Если отправка сообщения одному из игроков завершилась ошибкой.
        """
        if game_id not in self.game_players:
            raise KeyError(f"Игра с ID {game_id} не найдена.")
        
        for ws in self.game_players[game_id].values():
            try:
                await ws.send_json(message)
            except Exception as e:
                raise RuntimeError(f"Ошибка при отправке сообщения игроку.") from e
