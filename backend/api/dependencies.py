from backend.api.managers.connection_managaer import ConnectionManager
from backend.api.managers.game_manager import GameManager

game_manager = GameManager()
connection_manager = ConnectionManager()


def get_game_manager() -> GameManager:
    """Возвращает синглтон-экземпляр GameManager."""
    return game_manager


def get_connection_manager() -> ConnectionManager:
    """Возвращает синглтон-экземпляр ConnectionManager."""
    return connection_manager 