from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Dict, Any, Union

from backend.app.models.card import Card

# Типы действий игрока
class PlayerAction(Enum):
    READY = auto()
    JOIN = auto()
    ATTACK = auto()
    DEFEND = auto()
    COLLECT = auto()
    PASS = auto()
    QUIT = auto()

# Структура для ввода от игрока
@dataclass
class PlayerInput:
    player_id: int
    action: PlayerAction
    attack_card: Optional[Card] = None
    defend_card: Optional[Card] = None

def __str__(self):
    action_str = self.action.name
    card_info = ""
    if self.attack_card:
        card_info += f" attacking with {self.attack_card}"
    if self.defend_card:
        card_info += f" defending with {self.defend_card}"
    return f"Player {self.player_id} performs {action_str}{card_info}"


# Результаты выполнения действий
class ActionResult(Enum):
    SUCCESS = auto()
    INVALID_CARD = auto()
    INVALID_ACTION = auto()
    ROOM_FULL = auto()
    NOT_YOUR_TURN = auto()
    GAME_OVER = auto()
    CARD_REQUIRED = auto()  # Когда действие требует карту, но она не предоставлена
    CANNOT_BEAT = auto()    # Когда карта не может побить атакующую карту
    WRONG_CARD = auto()     # Когда карта не соответствует правилам подкидывания
    TABLE_FULL = auto()     # Когда на столе нет места для карты

# Структура для результата обработки ввода
@dataclass
class StateResponse:
    result: ActionResult
    message: str
    next_state: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    
    def __str__(self):
        return f"Result: {self.result.name} - {self.message}"

@dataclass
class StateTransition:
    """Класс для хранения информации о переходе между состояниями"""
    previous_state: Optional[str]
    new_state: str
    exit_info: Dict[str, Any]
    enter_info: Dict[str, Any]

    def __str__(self):
        return (f"Transition from {self.previous_state or 'None'} to {self.new_state}\n"
                f"Exit info: {self.exit_info}\n"
                f"Enter info: {self.enter_info}")
