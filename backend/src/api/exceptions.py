class GameManagerError(Exception):
    """Базовое исключение"""

    pass


class GameNotFoundError(GameManagerError):
    """Игра не найдена"""

    pass


class PlayerAlreadyInGameError(GameManagerError):
    """Игрок уже в игре"""

    pass


class PlayerNotInGameError(GameManagerError):
    """Игрок не в игре"""

    pass
