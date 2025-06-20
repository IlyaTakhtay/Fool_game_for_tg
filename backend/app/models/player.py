from typing import Set, Optional
from dataclasses import dataclass, field
from enum import Enum, auto

from backend.app.models.card import TrumpCard, Card, Suit, Rank  # TODO: fix path
from backend.app.utils.logger import setup_logger


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
        print("!!! remove_card CALLED !!!")
        logger = setup_logger("remove_card_logger")
        logger.info(f"Trying to remove card: {card} (rank={card.rank} id={id(card.rank)} type={type(card.rank)}), (suit={card.suit} id={id(card.suit)} type={type(card.suit)}) from hand:")
        for c in self._hand:
            logger.info(f"  Card in hand: {c} (rank={c.rank} id={id(c.rank)} type={type(c.rank)}), (suit={c.suit} id={id(c.suit)} type={type(c.suit)})")
            logger.info(f"    card == c: {card == c}, card is c: {card is c}, hash(card): {hash(card)}, hash(c): {hash(c)}")
            logger.info(f"    card.rank module: {card.rank.__module__}, c.rank module: {c.rank.__module__}")
            logger.info(f"    card.suit module: {card.suit.__module__}, c.suit module: {c.suit.__module__}")
        if card in self._hand:
            self._hand.remove(card)
            logger.info("Card removed successfully!")
        else:
            logger.error("Card not found in hand!")
            raise ValueError("Card is not in hand")

    def clear_hand(self) -> None:
        """Очистить руку"""
        self._hand.clear()
