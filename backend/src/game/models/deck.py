import random
from typing import List, Optional, Dict, Any

from backend.src.game.models.card import TrumpCard, Card, Suit, Rank


class Deck:
    _cards: List[Card]
    _trump_card: Optional[Card]
    _trump_suit: Optional[Suit]

    def __init__(self) -> None:
        self._cards = []
        self._trump_card = None
        self._trump_suit = None

    def generate_deck(self) -> None:
        self._trump_suit = random.choice(list(Suit))
        self._cards = [
            Card(rank, suit) if suit != self._trump_suit else TrumpCard(rank, suit)
            for suit in Suit
            for rank in Rank
        ]
        self._trump_card = random.choice(
            list(filter(lambda x: isinstance(x, TrumpCard), self._cards))
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "_cards": [card.to_dict() for card in self._cards],
            "_trump_card": self._trump_card.to_dict() if self._trump_card else None,
            "_trump_suit": self._trump_suit.value if self._trump_suit else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Deck":
        deck = cls()
        deck._cards = [
            Card.from_dict(card_data, trump_suit=Suit(data["_trump_suit"]))
            for card_data in data["_cards"]
        ]
        deck._trump_card = (
            Card.from_dict(data["_trump_card"], trump_suit=Suit(data["_trump_suit"]))
            if data["_trump_card"]
            else None
        )
        deck._trump_suit = Suit(data["_trump_suit"]) if data["_trump_suit"] else None
        return deck
