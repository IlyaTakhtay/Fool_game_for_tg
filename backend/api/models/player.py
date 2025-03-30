from enum import Enum, auto
from typing import Set
# Here is Pydantic models
class PlayerStatus(Enum): #TODO: хз че по статусам
    JOIN = auto()
    DISCONNECT = auto()
    READY = auto()
    NOT_READY = auto()

class Player:
    """Базовый класс для игрока"""
    def __init__(self,  id: str, name: str) -> None:
        self.id: str = id #get somewhere index
        # имя узнаем из бд ?
        self.staus: PlayerStatus = PlayerStatus.NOT_READY
        self._hand: Set[Card] = set()
