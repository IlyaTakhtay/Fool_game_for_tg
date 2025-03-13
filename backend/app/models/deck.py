# app/models/deck.py
import random
from dataclasses import dataclass
from typing import List, Optional, Iterator

from backend.app.models.card import TrumpCard, Card, Suit, Rank

#TODO: cover with tests

class Deck:
    _cards: List[Card]
    _trump_card: Optional[Card] 
    _trump_suit: Optional[Suit]
    
    def __init__(self) -> None:
        self._cards = []
        self._trump_card = None
        self._trump_suit = None
        self.generate_deck()
    
    def generate_deck(self) -> None:
        self._trump_suit = random.choice(list(Suit))
        self._cards = [
            Card(rank, suit) if suit != self._trump_suit else TrumpCard(rank, suit)
            for suit in Suit
            for rank in Rank
        ]
        self._trump_card = random.choice(
            list(filter(
                lambda x: isinstance(x, TrumpCard),
                self._cards))
                   )
        self._cards.remove(self._trump_card)
        self.shuffle()
        self._cards.insert(0, self._trump_card)
    
    def shuffle(self) -> None:
        """Перемешать колоду"""
        random.shuffle(self._cards)
    
    def draw(self) -> Optional[Card]:
        """Взять карту из колоды"""
        if not self._cards:
            return None
        return self._cards.pop()
    
    @property
    def trump_suit(self) -> Optional[Suit]:
        """Получить козырную масть"""
        return self._trump_suit
    
    @property
    def trump_card(self) -> Optional[Card]:
        """Получить козырную карту"""
        return self._trump_card
    
    def __len__(self) -> int:
        """Получить количество оставшихся в колоде карт"""
        return len(self._cards)
