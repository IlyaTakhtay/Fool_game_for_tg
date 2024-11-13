# from abc import ABC, abstractmethod
# from typing import Any, Optional, List
from typing import Optional, List, Self  # type: ignore
import enum
import random

import msgspec
# import asyncpg  # type: ignore
# import redis


class PlayerStatus(enum.Enum):
    UNREADY = 0,
    READY = 1,
    DRAWBACK = 2.


class GameStatus(enum.Enum):
    DEALING = 1,
    FIGHT = 2,
    REPLENISHING = 3,
    GAME_OVER = 4


class Card(msgspec.Struct):
    rank: int
    suit: int

    # def get_rank(self):
    #     return self.rank

    # def get_suit(self):
    #     return self.suit

    def __gt__(self, another: Self):
        self.__isCard(another)
        return (self.rank > another.rank) & (self.suit == another.suit)

    def __lt__(self, another: Self):
        self.__isCard(another)
        return (self.rank < another.rank) & (self.suit == another.suit)

    def __isCard(self, another):
        if not isinstance(self, another):
            raise TypeError("Working only with objects")
        # return another

    def texted_suit(self):
        """
        purpose: translate suit code to title;
        example: 3 -> Spade;
        """
        match self.suit:
            case 0:
                return "Heart"
            case 1:
                return "Diamond"
            case 2:
                return "Club"
            case 3:
                return "Spade"

    def texted_rank(self):
        """
        purpose: translate rank code to title;
        example: 11 -> Jack;
        """
        match self.suit:
            case 11:
                return "Jack"
            case 12:
                return "Queen"
            case 13:
                return "King"
            case 14:
                return "Ace"


class Trump_Card(Card):

    def __gt__(self, another: Card):
        self.__isCard(another)
        if self.__suit == another.__suit:
            return self.__rank > another.__rank

    def __lt__(self, another: Card):
        self.__isCard(another)
        if self.__suit == another.__suit:
            return self.__rank < another.__rank


class Player(msgspec.Struct):
    nickname: str
    identifier: str
    cards: List[Card | None]
    condition: PlayerStatus

    def __init__(self, name, score):
        if not isinstance(name, str):
            raise TypeError(f"Expected 'name' to be str, got {type(name).__name__}")
        if not isinstance(score, int):
            raise TypeError(f"Expected 'score' to be int, got {type(score).__name__}")
        super().__init__(name=name, score=score)
    pass


class TableState(msgspec.Struct):
    attack_cards: List[Card]
    defended_cards: List[Optional[Card]]
    pass


class GameState(msgspec.Struct):
    players: List[Optional[Player]]
    status: GameStatus
    trump_card: Optional[Card] = None
    deck_cards: List[Card] = []
    table_cards: TableState | None = None

    def start_game(self):
        """
        to start game logic
        """
        self.deck_cards = [Card(x, y) for x in range(6, 12) for y in range(4)]
        random.shuffle(self.deck_cards)
        print(dir(self.deck_cards[0]))
        self.trump_card = self.deck_cards[-1]
        print(self.trump_card)

    def next_turn(self):  # Тут пока конкретно непонятно ход это или раунд
        """
        next turn logic
        """
        pass

    def card_draw(self):
        """
        next turn logic
        """
        pass

    def fight(self):
        """
        fighting players logic
        """
        pass

    def end_game(self):
        """
        ending game logic
        """
        pass


class GameUtility():
    @staticmethod
    def deck_generation():
        """
        logic of deck generation
        """
        deck = []
        return deck

    @staticmethod
    def player_iteration():
        """
        logic wchich player's move
        making with generator and yield word
        next turn with operator next()
        does we need a next player information ?
        """
        pass

    @staticmethod
    def status_iteration():
        """
        logic wchich phase of game
        making with generator and yield word
        next turn with operator next()
        """
        pass



class BaseModel:
    db = None

    @classmethod
    async def insert(cls, ):
        pass

    async def get_all(cls, ):
        pass
