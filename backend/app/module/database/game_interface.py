# from abc import ABC, abstractmethod
# from typing import Any, Optional, List
from typing import Optional, Self, Generator  # type: ignore
import enum
import random

import msgspec
# import asyncpg  # type: ignore
# import redis


class PlayerStatus(enum.Enum):
    UNREADY = 0,
    READY = 1,
    DEFENDED = 2
    DRAWBACK = 3.


class GameStatus(enum.Enum):
    FIGHT = 1,
    END_TURN = 2,
    REPLENISHING = 3,
    GAME_OVER = 4


class Suit(enum.Enum):
    HEART = 0
    DIAMOND = 1
    CLUB = 2
    SPADE = 3


class Rank(enum.Enum):
    # ONE = 1
    # TWO = 2
    # THREE = 3
    # FOUR = 4
    # FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


class Card(msgspec.Struct, frozen=True):
    __rank: int
    __suit: Suit

    def __post_init__(self):
        if not isinstance(self.__rank, int):
            raise TypeError("Expected int object")
        if not isinstance(self.__suit, Suit):
            raise TypeError("Expected Suit obejct")
        if self.__suit.value > 3 or self.__suit.value < 0:
            raise ValueError("Suit except value from 0 to 3")
        if self.__rank > 14 or self.__rank < 6:
            raise ValueError("Rank except value from 6 to 14")

    @property
    def rank(self):
        return self._rank

    @property
    def suit(self):
        return self._suit

    def __gt__(self, another: Self):
        self.__isCard(another)
        return (self.__rank > another.rank) and (self.__suit == another.suit)

    def __lt__(self, another: Self):
        self.__isCard(another)
        return (self.__rank < another.rank) and (self.__suit == another.suit)

    def __isCard(self, another):
        if not isinstance(self, another):
            raise TypeError("Except Card object")
    
    def __eq__(self, another: Self):
        self.__isCard(another)
        return (another.rank == self.rank) and (another.suit == self.suit)

    def texted_suit(self):
        """
        **Purpose:** translate suit code to title;
        **Example:** 3 -> Spade;

        Returns:
            str: The translated suit title.
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
        **Purpose:** Translate rank code to title.
        **Example:** 11 -> Jack.

        Returns:
            str: The translated rank title.
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


class Trump_Card(Card, frozen=True):

    def __gt__(self, another: Card):
        self.__isCard(another)
        if self.__suit == another.__suit:
            return self.__rank > another.__rank

    def __lt__(self, another: Card):
        self.__isCard(another)
        if self.__suit == another.__suit:
            return self.__rank < another.__rank


class Player(msgspec.Struct):
    __nickname: str
    __identifier: str
    status: PlayerStatus
    __cards: set[Card | None]

    @property
    def identifier(self):
        return self.__identifier

    @property
    def nickname(self):
        return self.__nickname

    @property
    def cards(self):
        return self.__cards

    def add_card(self, cards: set[Card] | Card):
        if isinstance(cards, set):
            for card in cards:
                self.__cards.add(card)
        if isinstance(cards, Card):
            self.__cards.add(cards)

    def remove_card(self, cards: set[Card] | Card):
        if isinstance(cards, set):
            for card in cards:
                self.__cards.remove(card)
        if isinstance(cards, Card):
            self.__cards.remove(cards)

    def has_card(self, input_card: Card) -> bool:
        for card in self.cards:
            return card == input_card
        return False

    def __eq__(self, player: Self):
        if isinstance(self, player):
            return self.identifier == player.identifier


class TableState(msgspec.Struct):
    __table_cards: list[tuple[Card, Optional[Card]]] = []
    cards_limit: int = 5

    @property
    def table_cards(self):
        return self.__table_cards

    def __is_valid_to_throw(self, input_card: Card) -> bool:
        """
        Makes checking for rules:
        - is there any card with same rank
        """
        if not self.table_cards:  # if our card first to put
            return True
        flattend_list = filter(
            lambda x: x is not None,
            sum(self.__table_cards, [])
            )
        if (input_card.rank in flattend_list and
                len(self.get_attack_cards()) < self.cards_limit):
            return True
        return False

    def add_attack_card(self, cards: list[Card] | Card) -> None:
        """
        Adds one or more attack cards to the table with no associated
        defend cards.
        Args:
            cards (list[Card] | Card): A single Card object or a list of Card objects to be added as attack cards.
        Raises:
            TypeError: If the provided argument is neither a Card nor a list of Cards.
        """
        cards = cards if isinstance(cards, list) else [cards]
        for card in cards:
            if self.__is_valid_to_throw(card):
                self.__table_cards.append((card, None))

    def __is_valid_to_defend(
        self,
        attack_card: Card,
        defend_card: Card
    ) -> bool:
        """
        Makes checking for rules:
        - is it possible to cover this attack with this def card
        """
        if attack_card > defend_card:
            return False
        return True

    def add_defend_card(self, attack_card: Card, defend_card: Card) -> None:
        """
        Adds defend card with associated attack card
        Args:
            attack_card: Card
            defend_card: Card
        """
        if isinstance(attack_card, Card) and isinstance(defend_card, Card):
            for i, (table_attack_card, _) in enumerate(self.__table_cards):
                if attack_card == table_attack_card:
                    if self.__is_valid_to_defend(attack_card, defend_card):
                        self.__table_cards[i] = (attack_card, defend_card)
                elif defend_card == table_attack_card:
                    if self.__is_valid_to_defend(defend_card, attack_card):
                        self.__table_cards[i] = (defend_card, attack_card)


    # def add_pair_card()

    def get_attack_cards(self) -> list[Card]:
        return [attack_card for attack_card, _ in self.__table_cards]

    def get_defend_cards(self) -> list[Optional[Card]]:
        return [defend_card for _, defend_card in self.__table_cards]

    def clear_table(self) -> None:
        self.__table_cards.clear()


class GameState(msgspec.Struct):
    room_size: int
    players_sequence = None
    players: list[Player] = []  # safety,check msgspec to approve
    status: GameStatus | None = None
    trump_card: Optional[Card | Suit] = None
    deck_cards: list[Card | Trump_Card] = []  # safety,check msgspec to approve
    table_state: TableState = TableState()
    cards_fall: bool = False

    def __deck_generation(self):
        trump_suit = random.choice(list(Suit))
        for rank in range(6, 15):
            for suit in Suit:
                if suit == trump_suit:
                    self.deck_cards.append(Trump_Card(rank, suit))
                else:
                    self.deck_cards.append(Card(rank, suit))
        self.trump_card = random.choice(
            list(filter(
                lambda x: isinstance(x, Trump_Card),
                self.deck_cards))
                   )
        random.shuffle(self.deck_cards)

    def __get_min_trump_card(self, player: Player) -> list[Trump_Card] | None:
        """
        Returns the lowest trump card in the player's hand.
        """
        trump_cards = filter(lambda card:
                             isinstance(card, Trump_Card), player.cards)
        if trump_cards:
            return min(trump_cards, default=None)
        return None

    def __get_who_goes_first(self) -> Player:
        min_card = None
        first_player = None

        for player in self.players:
            player_min_card = self.__get_min_trump_card(player)  
            if (min_card is not None and player_min_card < min_card):
                min_card = player_min_card
                first_player = player
        if first_player is None:
            return random.choice(self.players)
        return first_player

    def __find_player_by_identifier(self, identifier: str) -> Player:
        if isinstance(identifier, str):
            return next((player for player in self.players if player.identifier == identifier), None)
        else:
            raise TypeError("expected str")

    def update_player_status(self, data: list[Player] | Player) -> None:
        """
        Updates player status.
        Args:
            data: list of Player or only Player.
        """
        if not isinstance(data, (list, Player)):
            raise TypeError("Expected list of Players or Player")

        if isinstance(data, list):
            for data_player in data:
                game_player = self.__find_player_by_identifier(
                    data_player.identifier
                    )
                if game_player:
                    game_player.status = data_player.status
        else:
            game_player = self.__find_player_by_identifier(data.identifier)
            if game_player:
                game_player.status = data.status

    def add_player(self, player: Player) -> bool:
        if isinstance(player, Player):
            if len(self.players) < self.room_size:
                self.players.append(player)
                return True
            else:
                return False
        else:
            raise TypeError("Except Player type")

    def remove_player(self, player: Player | str):
        if isinstance(player, str):
            self.players.remove(self.__find_player_by_identifier(player))
        elif isinstance(player, Player):
            self.players.remove(player)
        else:
            raise TypeError("Except Player or string type")

    def __update_player_cards(self, input_player: Player | dict, action: str):
        for key, cards in (
            input_player.items()
            if isinstance(input_player, dict)
            else [(input_player.identifier, input_player.cards)]
        ):
            player = self.__find_player_by_identifier(key)
            if action == "add":
                player.add_card(set(cards))
            elif action == "remove":
                player.remove_card(set(cards))

    def add_card_to_player(self, input_player: Player | dict):
        self.__update_player_cards(input_player, "add")

    def delete_card_from_player(self, input_player: Player | dict):
        self.__update_player_cards(input_player, "remove")

    def __init_players_sequence(self, first_player: Player):
        first_player_index = self.players.index(first_player)
        self.players = (
            self.players[first_player_index:]
            + self.players[:first_player_index]
        )
        while True:
            for index, player in enumerate(self.players):
                yield index, player

    def start_game(self):
        """
        Logic executing:
            generating deck
            getting players positions on table
            drawing cards
            generating which player's turn first
            generating players turn iterator
        """
        self.__deck_generation()
        for player in self.players:  # filling player's hand
            self.fill_player_cards(player)
        first_player = self.__get_who_goes_first()  # выбрали игрока атакующего
        self.players_sequence = self.__init_players_sequence(first_player)  
        # запустили генерацию хода
        print(next(self.players_sequence))
        # создаем итератор по ходам игроков

    def fill_player_cards(self, player: Player):
        """
        Logic to only fill player's hand
        This doesn't have logic for operating the sequence of drawing
        """
        while self.deck_cards and len(player.cards) < 6:
            player.cards.append(self.deck_cards.pop())
        if self.deck_cards and isinstance(self.trump_card, Trump_Card):
            self.trump_card = self.trump_card.suit

    def player_drawback(self, player: Player):
        if (len(self.table_state.get_attack_cards()) !=
                len(self.table_state.get_defend_cards())):
            player.add_card(set(self.deck_cards))
            self.table_state.clear_table()

    def next_turn(self):
        """
        Logic to prepare game area to next turn
        """
        if self.players_sequence

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
    def hand_filter(player: Player):
        """
        logic of hand to filter cards
        """

    @staticmethod
    def player_iteration():
        """
        logic wchich player's move
        making with generator and yield word
        next turn with operator next()
        does we need a next player information ?
        а здесь разве можем ? нам же нужен доступ к списку игроков
        """
        pass

    @staticmethod
    def status_iteration():
        """
        logic wchich phase of game
        making with generator and yield word
        next turn with operator next()
        а тут к текущему статусу, а нет, но хранить то где-то надо итератор, или нет ? надо же
        """
        pass



# class BaseModel:
#     db = None

#     @classmethod
#     async def insert(cls, ):
#         pass

#     async def get_all(cls, ):
#         pass
