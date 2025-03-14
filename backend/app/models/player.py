from typing import Set, Optional
from dataclasses import dataclass, field
from enum import Enum, auto

from backend.app.models.card import TrumpCard, Card, Suit, Rank #TODO: fix path


class PlayerStatus(Enum): #TODO: хз че по статусам
    NOT_READY = auto()
    READY = auto()
    EMPTY = auto()
    VICTORY = auto()


class Player:
    """Базовый класс для игрока"""
    def __init__(self,  id: str, name: str) -> None:
        self.id: str = id #get somewhere index
        self._status: PlayerStatus = PlayerStatus.NOT_READY
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
            raise ValueError('Card is already in hand')
    
    def get_cards(self) -> Set[Card]:
        return self._hand

    def remove_card(self, card: Card) -> None:
        """Удалить карту из руки"""
        if card in self._hand:
            self._hand.remove(card)
        else:
            raise ValueError('Card is not in hand')
        
    def clear_hand(self) -> None:
        """Очистить руку"""
        self._hand.clear()

    # def is_hand_full(self, cls) -> bool:
    #     """Проверить, полная ли рука"""
    #     if len(self._hand) >= cls.hand_limit:
    #         return True
    #     return False
