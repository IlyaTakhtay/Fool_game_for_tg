from dataclasses import dataclass
from enum import Enum
from typing_extensions import Self


class Suit(Enum):
    HEARTS = "H"
    DIAMONDS = "D"
    CLUBS = "C"
    SPADES = "S"


class Rank(Enum):
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit

    def __gt__(self, another: Self):
        if self.suit != another.suit:
            return NotImplemented
        return self.rank.value > another.rank.value

    def __lt__(self, another: Self):
        if self.suit != another.suit:
            return NotImplemented
        return self.rank.value < another.rank.value

    def __eq__(self, another: object):
        if not isinstance(another, Card):
            return NotImplemented
        return (another.rank == self.rank) and (another.suit == self.suit)

    def __str__(self):
        return f"{self.rank.name} of {self.suit.name}"

    def to_dict(self):
        return {"rank": self.rank, "suit": self.suit}

    @staticmethod
    def from_dict(data, trump_suit=None):
        rank = data['rank']
        suit = data['suit']
        # Преобразуем rank
        if isinstance(rank, str):
            if rank.isdigit():
                rank = Rank(int(rank))
            else:
                rank = Rank[rank]  # 'SIX' -> Rank.SIX
        else:
            rank = Rank(rank)
        # Преобразуем suit
        if isinstance(suit, str):
            if len(suit) == 1:
                suit = Suit(suit)
            else:
                suit = Suit[suit]  # 'SPADES' -> Suit.SPADES
        else:
            suit = Suit(suit)
        # Если это козырная масть — создаём TrumpCard
        if trump_suit is not None and suit == trump_suit:
            return TrumpCard(rank=rank, suit=suit)
        return Card(rank=rank, suit=suit)

    def __hash__(self):
        return hash((self.rank, self.suit))


@dataclass(frozen=True)
class TrumpCard(Card):

    def __gt__(self, another: Card) -> bool:
        if self.suit == another.suit:
            return self.rank.value > another.rank.value
        return True

    def __ge__(self, another: Card) -> bool:
        if self.suit == another.suit:
            return self.rank.value >= another.rank.value
        return True

    def __lt__(self, another: Card) -> bool:
        if self.suit == another.suit:
            return self.rank.value < another.rank.value
        return False

    def __le__(self, another: Card) -> bool:
        if self.suit == another.suit:
            return self.rank.value <= another.rank.value
        return False
