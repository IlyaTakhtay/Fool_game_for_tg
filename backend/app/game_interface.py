# # from abc import ABC, abstractmethod
# from typing import Any, Optional, List
# from dataclasses import dataclass
# from typing_extensions import Self
# from typing import Optional, Generator  # type: ignore
# import enum
# import random

# import logging

# import msgspec
# # import asyncpg  # type: ignore
# # import redis


# class PlayerStatus(enum.Enum):
#     UNREADY = 0
#     READY = 1
#     DEFENDED = 2
#     DRAWBACK = 3


# class GameStatus(enum.Enum):
#     GAME_FORMING = 0
#     FIGHT = 1
#     END_TURN = 2
#     REPLENISHING = 3
#     GAME_OVER = 4


# class Suit(enum.Enum):
#     HEART = 0
#     DIAMOND = 1
#     CLUB = 2
#     SPADE = 3


# class Rank(enum.Enum):
#     SIX = 6
#     SEVEN = 7
#     EIGHT = 8
#     NINE = 9
#     TEN = 10
#     JACK = 11
#     QUEEN = 12
#     KING = 13
#     ACE = 14



# @dataclass(frozen=True)
# class Card():
#     _rank: Rank
#     _suit: Suit

#     @property
#     def rank(self):
#         return self._rank

#     @property
#     def suit(self):
#         return self._suit

#     def __gt__(self, another: Self):
#         self._isCard(another)
#         return (self._rank > another.rank) and (self._suit == another.suit)

#     def __lt__(self, another: Self):
#         self._isCard(another)
#         return (self._rank < another.rank) and (self._suit == another.suit)

#     def _isCard(self, another):
#         if not isinstance(another, Card):
#             raise TypeError("Except Card object")

#     def __eq__(self, another: Self):
#         self._isCard(another)
#         return (another.rank == self.rank) and (another.suit == self.suit)

#     def __str__(self):
#         print(f"{self._rank.name} of {self._suit.name}")

# @dataclass(frozen=True)
# class Trump_Card(Card):

#     def __post_init__(self):
#         return super().__post_init__()

#     def __gt__(self, another: Card):
#         self._isCard(another)
#         if self._suit == another._suit:
#             return self._rank > another._rank
#         return False

#     def __lt__(self, another: Card):
#         self._isCard(another)
#         if self._suit == another._suit:
#             return self._rank < another._rank
#         return False


# player_fields_client = {
#     "_nickname": "nickname",
#     "_identifier": "id",
#     "status": "status",
#     "_cards": "cards"
# }


# class Player(msgspec.Struct, rename=player_fields_client):
#     _nickname: str
#     _identifier: str
#     status: PlayerStatus = PlayerStatus.UNREADY
#     _cards: list[Card | None] = msgspec.field(default_factory=list)

#     @property
#     def nickname(self):
#         return self._nickname

#     @nickname.setter
#     def nickname(self, val):
#         # self.nickname = val
#         raise AttributeError("is private")

#     @property
#     def identifier(self):
#         return self._identifier

#     @property
#     def cards(self):
#         return self._cards

#     def get_trump_cards(self):
#         return [card for card in self.cards if isinstance(card, Trump_Card)]

#     def add_card(self, cards: list[Card] | Card):
#         if isinstance(cards, list):
#             self._cards.extend(cards)
#         elif isinstance(cards, Card):
#             self._cards.append(cards)

#     def remove_card(self, cards: list[Card] | Card):
#         if isinstance(cards, list):
#             for card in cards:
#                 self._cards.remove(card)
#         elif isinstance(cards, Card):
#             self._cards.remove(cards)

#     def has_card(self, input_card: Card) -> bool:
#         return input_card in self.cards

#     def __eq__(self, player: Self):
#         if isinstance(player, Player):
#             return self.identifier == player.identifier


# class TableState(msgspec.Struct):
#     __table_cards: list[
#         tuple[Card, Optional[Card]]
#         ] = msgspec.field(default_factory=list)
#     cards_limit: int = 5

#     @property
#     def table_cards(self):
#         return self.__table_cards

#     def __is_valid_to_throw(self, input_card: Card) -> bool:
#         """
#         Makes checking for rules:
#         - is there any card with same rank
#         """
#         if not self.table_cards:  # if our card first to put
#             return True
#         flattend_list = filter(
#             lambda x: x is not None,
#             sum(self.__table_cards, [])
#             )
#         if (input_card.rank in flattend_list and
#                 len(self.get_attack_cards()) < self.cards_limit):
#             return True
#         return False

#     def add_attack_card(self, cards: list[Card] | Card) -> None:
#         """
#         Adds one or more attack cards to the table with no associated
#         defend cards.
#         Args:
#             cards (list[Card] | Card): A single Card object or a list of
#             Card objects to be added as attack cards.
#         Raises:
#             TypeError: If the provided argument is neither a Card nor a list
#             of Cards.
#         """
#         cards = cards if isinstance(cards, list) else [cards]
#         for card in cards:
#             if self.__is_valid_to_throw(card):
#                 self.__table_cards.append((card, None))

#     def __is_valid_to_defend(
#         self,
#         attack_card: Card,
#         defend_card: Card
#     ) -> bool:
#         """
#         Makes checking for rules:
#         - is it possible to cover this attack with this def card
#         """
#         if attack_card > defend_card:
#             return False
#         return True

#     def add_defend_card(self, attack_card: Card, defend_card: Card) -> None:
#         """
#         Adds defend card with associated attack card
#         Args:
#             attack_card: Card
#             defend_card: Card
#         """
#         if isinstance(attack_card, Card) and isinstance(defend_card, Card):
#             for i, (table_attack_card, _) in enumerate(self.__table_cards):
#                 if attack_card == table_attack_card:
#                     if self.__is_valid_to_defend(attack_card, defend_card):
#                         self.__table_cards[i] = (attack_card, defend_card)
#                 elif defend_card == table_attack_card:
#                     if self.__is_valid_to_defend(defend_card, attack_card):
#                         self.__table_cards[i] = (defend_card, attack_card)
#     # def add_pair_card()

#     def get_attack_cards(self) -> list[Card]:
#         return [attack_card for attack_card, _ in self.__table_cards]

#     def get_defend_cards(self) -> list[Optional[Card]]:
#         return [defend_card for _, defend_card in self.__table_cards]

#     def clear_table(self) -> None:
#         self.__table_cards.clear()



# class GameState(msgspec.Struct):
#     game_id: int
#     room_size: int
#     password: str | None = None
#     status: GameStatus | None = None
#     players_sequence: Generator | None = None
#     attack_player_id: int | None = None
#     players: list[Player] = msgspec.field(default_factory=list)
#     trump_card: Optional[Card | Suit] = None
#     deck_cards: list[Card | Trump_Card] = msgspec.field(default_factory=list)
#     table_state: TableState = msgspec.field(default_factory=TableState)
#     cards_fall: bool = False

#     def __hash__(self):
#         return self.game_id

#     def __deck_generation(self):
#         trump_suit = random.choice(list(Suit))
#         for rank in range(6, 15):
#             for suit in Suit:
#                 if suit == trump_suit:
#                     self.deck_cards.append(Trump_Card(rank, suit))
#                 else:
#                     self.deck_cards.append(Card(rank, suit))
#         self.trump_card = random.choice(
#             list(filter(
#                 lambda x: isinstance(x, Trump_Card),
#                 self.deck_cards))
#                    )
#         random.shuffle(self.deck_cards)

#     def __get_min_trump_card(self, player: Player) -> list[Trump_Card] | None:
#         """
#         Returns the lowest trump card in the player's hand.
#         """
#         trump_cards = filter(lambda card:
#                              isinstance(card, Trump_Card), player.cards)
#         if trump_cards:
#             return min(trump_cards, default=None)
#         return None

#     def __get_who_goes_first(self) -> Player:
#         min_card = None
#         first_player = None

#         for player in self.players:
#             player_min_card = self.__get_min_trump_card(player)
#             if (min_card is not None and player_min_card < min_card):
#                 min_card = player_min_card
#                 first_player = player
#         if first_player is None:
#             return random.choice(self.players)
#         return first_player

#     def __find_player_by_identifier(self, identifier: str) -> Player | None:
#         if isinstance(identifier, str):
#             return next((
#                 player for player in self.players if
#                 player.identifier == identifier), None)
#         else:
#             raise TypeError("expected str")

#     def update_player_status(self, data: list[Player] | Player) -> None:
#         """
#         Updates player status.
#         Args:
#             data: list of Player or only Player.
#         """
#         if not isinstance(data, (list, Player)):
#             raise TypeError("Expected list of Players or Player")

#         if isinstance(data, list):
#             for data_player in data:
#                 game_player = self.__find_player_by_identifier(
#                     data_player.identifier
#                     )
#                 if game_player:
#                     game_player.status = data_player.status
#         else:
#             game_player = self.__find_player_by_identifier(data.identifier)
#             if game_player:
#                 game_player.status = data.status

#     def add_player(self, player: Player) -> bool:
#         if not isinstance(player, Player):
#             raise TypeError("Except Player type")
#         elif all(player.identifier
#                  != game_player.identifier for game_player in self.players):
#             if len(self.players) < self.room_size:
#                 self.players.append(player)
#                 return True
#         return False

#     def remove_player(self, player: Player | str):
#         if isinstance(player, str):
#             if pl := self.__find_player_by_identifier(player):
#                 self.players.remove(pl)
#         elif isinstance(player, Player):
#             self.players.remove(player)
#         else:
#             raise TypeError("Except Player or string type")

#     def __update_player_cards(self, input_player: Player | dict, action: str):
#         for key, cards in (
#             input_player.items()
#             if isinstance(input_player, dict)
#             else [(input_player.identifier, input_player.cards)]
#         ):
#             player = self.__find_player_by_identifier(key)
#             if action == "add" and player:
#                 player.add_card(cards)
#             elif action == "remove" and player:
#                 player.remove_card(cards)

#     def __is_valid_to_attack(self, player: Player) -> bool:
#         game_player = self.__find_player_by_identifier(player.identifier)
#         if game_player is not None:
#             return (
#                 self.status == GameStatus.FIGHT
#                 and player.identifier == self.attack_player_id
#                 and all(game_player.has_card(card) for card in player.cards)
#                 )
#         return False

#     def __is_valid_to_defend(self, player: Player) -> bool:
#         game_player = self.__find_player_by_identifier(
#             str(self.attack_player_id)
#             )

#         if game_player is not None:
#             index_of_found_player = self.players.index(game_player)
#             defend_player = self.players[
#                 (index_of_found_player + 1) % len(self.players)]

#             return (
#                 player.identifier == defend_player.identifier
#                 and all(defend_player.has_card(card) for card in player.cards)
#                 )

#         return False

#     def add_card_to_player(self, input_player: Player | dict):
#         self.__update_player_cards(input_player, "add")

#     def delete_card_from_player(self, input_player: Player | dict):
#         self.__update_player_cards(input_player, "remove")

#     def data_communication(self, data: Player, extention: Card | None):
#         if isinstance(data, Player):
#             # ТУТ СРАЗУ ПРОВЕРЯЕМ ЕСТЬ ЛИ У НАС ТАКОЙ ИГРОК, ЕСЛИ НЕТ ТО ГГ
#             # А ЕСЛИ ДА, ТО МОЖЕМ ПЕРЕДАВАТЬ ВО ВСЕ ДРУГИЕ ФУНКЦИИ И НЕ ДРОЧИТЬ ПОИСК ИГРОКА ПО ТЫЩУ РАЗ
#             if data.status:
#                 self.update_player_status(data=data)
#                 status_result = {data.identifier, data.status}
#             if data.cards:
#                 if self.__is_valid_to_attack(data):
#                     self.table_state.add_attack_card(data.cards)
#                     self.delete_card_from_player(data.cards)
#                     table_cards = self.table_state.table_cards
#                 elif self.__is_valid_to_defend(data) and extention:
#                     self.table_state.add_defend_card(extention, data.cards)
#                     self.delete_card_from_player(data.cards)
#                     pl = self.__find_player_by_identifier(data.identifier)
#                     if pl: # это бы пораньше перенести и всю логику перелопатить. ВООБЩЕ САМОй ПЕРВОЙ ПРОВВЕРКОЙ ДОЛЖНО БЫТЬ
#                         player_cards = pl.cards
#             return status_result, table_cards, player_cards

#     def __clear_all_player_status(self):
#         for player in self.players:
#             player.status = PlayerStatus.UNREADY

#     def __init_players_sequence(self, first_player: Player):
#         first_player_index = self.players.index(first_player)
#         self.players = (
#             self.players[first_player_index:]
#             + self.players[:first_player_index]
#         )
#         while True:
#             for index, player in enumerate(self.players):
#                 self.attack_player_id = index
#                 yield index, player

#     def start_game(self):
#         """
#         Logic executing:
#             generating deck
#             getting players positions on table
#             drawing cards
#             generating which player's turn first
#             generating players turn iterator
#         """
#         self.__deck_generation()
#         for player in self.players:  # filling player's hand
#             self.replish_player_cards(player)
#         first_player = self.__get_who_goes_first()  # выбрали игрока атакующего
#         self.players_sequence = self.__init_players_sequence(first_player)
#         # запустили генерацию хода
#         # logging.debug(f"SESSSSS{[player.get_trump_cards() for player in self.players]}")
#         # logging.debug(f"SEXSEXSEX{next(self.players_sequence)}")
#         self.__clear_all_player_status()
#         # создаем итератор по ходам игроков

#     def replish_player_cards(self, player: Player):
#         """
#         Logic to only fill player's hand
#         This doesn't have logic for operating the sequence of drawing
#         """
#         while self.deck_cards and len(player.cards) < 6:
#             player.cards.append(self.deck_cards.pop())
#         if self.deck_cards and isinstance(self.trump_card, Trump_Card):
#             self.trump_card = self.trump_card.suit

#     def player_drawback(self, player: Player):
#         if (len(self.table_state.get_attack_cards()) !=
#                 len(self.table_state.get_defend_cards())):
#             player.add_card(self.deck_cards)

#     def __check_game_over(self) -> Player | bool:
#         """
#         Check end game condition and return loser
#         """
#         self.status = GameStatus.GAME_OVER
#         if (
#             sum(not pl.cards for pl in self.players) == len(self.players)-1 and
#             not self.deck_cards
#         ):
#             return next(pl for pl in self.players if pl.cards)
#         return False

#     def next_turn(self):  # короче тут прям дрисня какая-то и по code style и по логике, все переделать
#         """
#         Logic to prepare game area to next turn
#         """
#         def set_table_lim_comparable_hand_size():
#             if self.table_state.cards_limit > len(new_def.cards):
#                 self.table_state.cards_limit = len(new_def.cards)

#         if loser := self.__check_game_over():
#             return loser   # Игра завершена
#         # раздача карт игрокам
#         self.replish_player_cards(self.players[self.attack_player_id])
#         for player in (
#             self.players[self.attack_player_id:]
#             + self.players[:self.attack_player_id]
#         ):  # обходим всех игроков по очереди и раздаем им карты, начиная с защищавшегося
#             self.replish_player_cards(player)
#         _, def_player = next(self.players_sequence)
#         if def_player.status == PlayerStatus.DRAWBACK:
#             self.player_drawback()
#             _, new_def = next(self.players_sequence)
#             set_table_lim_comparable_hand_size()
#         else:
#             self.replish_player_cards(def_player)
#             self.cards_fall = True
#             self.table_state.cards_limit = 6  # если мы здесь-первое бито было
#             set_table_lim_comparable_hand_size()
#         self.table_state.clear_table()
#         self.__clear_all_player_status()

