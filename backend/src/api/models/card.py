#pydantic card
from dataclasses import dataclass
from typing_extensions import Self

from enum import Enum


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
class Card():
    rank: Rank
    suit: Suit

    def __gt__(self, another: Self):
        if self.suit != another.suit:
            return NotImplemented
        return (self.rank.value > another.rank.value)

    def __lt__(self, another: Self):
        if self.suit != another.suit:
            return NotImplemented
        return (self.rank.value < another.rank.value)
    
    def __eq__(self, another: object):
        if not isinstance(another, Card):
            return NotImplemented
        return (another.rank == self.rank) and (another.suit == self.suit)
            
    def __str__(self):
        return f"{self.rank.name} of {self.suit.name}"
