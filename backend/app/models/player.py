import logging
from typing import Set, Optional
from dataclasses import dataclass, field
from enum import Enum, auto

from backend.app.models.card import TrumpCard, Card, Suit, Rank  # TODO: fix path

logger = logging.getLogger(__name__)


class PlayerStatus(Enum):  # TODO: check statuses
    LEAVED = auto()
    UNREADY = auto()
    READY = auto()
    VICTORY = auto()


class Player:
    """Базовый класс для игрока"""

    def __init__(self, id_: str, name: str) -> None:
        self.id_: str = id_  # get somewhere uuid
        self._status: PlayerStatus = PlayerStatus.UNREADY
        self.name: str = name
        self._hand: Set[Card] = set()

    @property
    def status(self) -> PlayerStatus:
        return self._status

    @status.setter
    def status(self, status: PlayerStatus) -> None:
        self._status = status

    def add_card(self, card: Card) -> None:
        """Добавить карту в руку"""
        if not card in self._hand:
            self._hand.add(card)
        else:
            raise ValueError("Card is already in hand")

    def get_cards(self) -> Set[Card]:
        return self._hand

    def remove_card(self, card: Card) -> None:
        """Удалить карту из руки"""
        try:
            self._hand.remove(card)
        except KeyError:
            logger.error(
                f"Карта {card} не найдена в руке у игрока {self.id_}", exc_info=False
            )
            raise ValueError("Card is not in hand")

    def clear_hand(self) -> None:
        """Очистить руку"""
        self._hand.clear()
