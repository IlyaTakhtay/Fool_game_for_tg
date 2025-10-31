import gc
import json
import pickle
import random
import sys
import time
from functools import wraps
from pathlib import Path
from statistics import mean, stdev
from uuid import uuid4

import lz4
import msgspec

from backend.src.adapters.persistence.redis import RedisFoolGameAdapter
from backend.src.game.models.game import FoolGame
from backend.src.game.models.player import Player, PlayerStatus
from backend.src.game.models.card import Card, Suit, Rank, TrumpCard
from backend.src.game.models.deck import Deck
from backend.src.game.states.lobby_state import LobbyState
from backend.src.game.states.play_round_state import PlayRoundWithoutThrowState
from backend.src.game.states.game_over import GameOverState


def benchmark(iterations: int = 100, warmup: int = 10):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(warmup):
                func(*args, **kwargs)

            gc.collect()
            gc.disable()

            times = []
            for _ in range(iterations):
                start = time.perf_counter()
                func(*args, **kwargs)
                end = time.perf_counter()
                times.append(end - start)

            gc.enable()

            avg = mean(times)
            std = stdev(times) if len(times) > 1 else 0
            print(
                f"{func.__name__:30} | avg: {avg*1000:8.3f}ms | std: {std*1000:8.3f}ms"
            )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def measure_memory(games: list) -> dict:
    """Измеряет размер объектов в памяти."""
    total = sum(sys.getsizeof(game) for game in games)
    avg = total / len(games)
    return {
        "total_bytes": total,
        "total_mb": total / (1024 * 1024),
        "avg_bytes": avg,
        "avg_kb": avg / 1024,
    }


def create_deck_with_trump(trump_suit: Suit) -> Deck:
    deck = Deck()
    deck._trump_suit = trump_suit
    cards = [
        Card(rank, suit) if suit != trump_suit else TrumpCard(rank, suit)
        for suit in Suit
        for rank in Rank
    ]
    random.shuffle(cards)
    deck._cards = cards
    try:
        deck._trump_card = next(c for c in cards if c.suit == trump_suit)
    except StopIteration:
        deck._trump_card = None
    return deck


def _create_players(names: list[str]) -> list[Player]:
    return [Player(id_=str(uuid4()), name=name) for name in names]


def _deal_cards(players: list[Player], cards_per_player: int, deck: Deck):
    for player in players:
        player.clear_hand()
        for _ in range(cards_per_player):
            if len(deck) > 0:
                player.add_card(deck.draw())


def scenario_1_lobby():
    game = FoolGame(game_id="lobby_game", players_limit=4)
    game.players = _create_players(["Alice", "Bob", "Charlie", "David"])
    game._current_state = LobbyState(game)
    return game


def scenario_2_early_game_2_players():
    game = FoolGame(game_id="early_game_2p", players_limit=2)
    players = _create_players(["Alice", "Bob"])
    game.players = players
    game.deck = create_deck_with_trump(Suit.DIAMONDS)
    _deal_cards(players, 6, game.deck)
    game.current_attacker_id = players[0].id_
    game.current_defender_id = players[1].id_
    game._current_state = PlayRoundWithoutThrowState(game)
    return game


def scenario_3_mid_game_attack():
    game = FoolGame(game_id="mid_game_attack", players_limit=3)
    players = _create_players(["Alice", "Bob", "Charlie"])
    game.players = players
    game.deck = create_deck_with_trump(Suit.CLUBS)
    _deal_cards(players, 6, game.deck)
    for _ in range(8):
        if len(game.deck) > 0:
            game.deck.draw()
    game.current_attacker_id = players[0].id_
    game.current_defender_id = players[1].id_

    # ИСПРАВЛЕНИЕ: Rank и Suit в правильном порядке
    game.game_table.table_cards.append(
        {"attack_card": Card(Rank.NINE, Suit.SPADES), "defend_card": None}
    )
    game.game_table.table_cards.append(
        {
            "attack_card": Card(Rank.TEN, Suit.HEARTS),
            "defend_card": Card(Rank.QUEEN, Suit.HEARTS),
        }
    )

    game._current_state = PlayRoundWithoutThrowState(game)
    return game


def scenario_4_mid_game_full_table():
    game = FoolGame(game_id="mid_game_full_table", players_limit=4)
    players = _create_players(["Alice", "Bob", "Charlie", "David"])
    game.players = players
    game.deck = create_deck_with_trump(Suit.HEARTS)
    _deal_cards(players, 6, game.deck)
    for _ in range(8):
        if len(game.deck) > 0:
            game.deck.draw()
    game.current_attacker_id = players[0].id_
    game.current_defender_id = players[1].id_

    # ИСПРАВЛЕНИЕ: Rank и Suit в правильном порядке
    table_card_pairs = [
        {
            "attack_card": Card(Rank.SIX, Suit.CLUBS),
            "defend_card": Card(Rank.TEN, Suit.CLUBS),
        },
        {
            "attack_card": Card(Rank.NINE, Suit.DIAMONDS),
            "defend_card": Card(Rank.JACK, Suit.DIAMONDS),
        },
        {
            "attack_card": Card(Rank.ACE, Suit.SPADES),
            "defend_card": TrumpCard(Rank.ACE, Suit.HEARTS),
        },
        {"attack_card": Card(Rank.EIGHT, Suit.CLUBS), "defend_card": None},
        {"attack_card": Card(Rank.EIGHT, Suit.DIAMONDS), "defend_card": None},
    ]
    game.game_table.table_cards.extend(table_card_pairs)

    game._current_state = PlayRoundWithoutThrowState(game)
    return game


def scenario_5_defender_takes():
    game = scenario_3_mid_game_attack()
    game.game_id = "defender_takes"
    return game


def scenario_6_late_game_no_deck():
    game = FoolGame(game_id="late_game", players_limit=3)
    players = _create_players(["Alice", "Bob", "Charlie"])
    game.players = players
    game.deck = create_deck_with_trump(Suit.HEARTS)
    game.deck._cards = []
    # ИСПРАВЛЕНИЕ: Rank и Suit в правильном порядке
    players[0].add_card(Card(Rank.ACE, Suit.SPADES))
    players[1].add_card(Card(Rank.KING, Suit.DIAMONDS))
    players[2].add_card(TrumpCard(Rank.SIX, Suit.HEARTS))
    players[2].add_card(Card(Rank.SEVEN, Suit.CLUBS))
    game.current_attacker_id = players[0].id_
    game.current_defender_id = players[1].id_
    game._current_state = PlayRoundWithoutThrowState(game)
    return game


def scenario_7_game_over():
    game = scenario_6_late_game_no_deck()
    game.game_id = "game_over"
    game.players[0].clear_hand()
    game.loser_ids = [p.id_ for p in game.players if len(p.get_cards()) > 0]
    game._current_state = GameOverState(game)
    return game


def scenario_8_full_lobby_6_players():
    game = FoolGame(game_id="full_lobby_6p", players_limit=6)
    players = _create_players(["P1", "P2", "P3", "P4", "P5", "P6"])
    for p in players:
        p.status = PlayerStatus.READY
    game.players = players
    game._current_state = LobbyState(game)
    return game


def scenario_9_one_on_one_final():
    game = FoolGame(game_id="one_on_one", players_limit=2)
    players = _create_players(["Alice", "Bob"])
    game.players = players
    game.deck = create_deck_with_trump(Suit.SPADES)
    game.deck._cards = []
    # ИСПРАВЛЕНИЕ: Rank и Suit в правильном порядке
    hand_alice = [
        TrumpCard(Rank.ACE, Suit.SPADES),
        Card(Rank.TEN, Suit.CLUBS),
        Card(Rank.KING, Suit.DIAMONDS),
    ]
    hand_bob = [
        TrumpCard(Rank.QUEEN, Suit.SPADES),
        Card(Rank.JACK, Suit.HEARTS),
        Card(Rank.ACE, Suit.DIAMONDS),
    ]
    for card in hand_alice:
        players[0].add_card(card)
    for card in hand_bob:
        players[1].add_card(card)
    game.current_attacker_id = players[0].id_
    game.current_defender_id = players[1].id_
    game._current_state = PlayRoundWithoutThrowState(game)
    return game


def scenario_10_long_game_discard_pile():
    game = scenario_4_mid_game_full_table()
    game.game_id = "long_game_discard"
    game.deck._cards = game.deck._cards[:5]
    for p in game.players:
        current_hand = list(p.get_cards())
        if len(current_hand) > 3:
            for card_to_remove in random.sample(current_hand, len(current_hand) - 3):
                p.remove_card(card_to_remove)
    return game


def generate_all_scenarios() -> list[FoolGame]:
    """Возвращает список всех игровых сценариев для бенчмарка."""
    return [
        scenario_1_lobby(),
        scenario_2_early_game_2_players(),
        scenario_3_mid_game_attack(),
        scenario_4_mid_game_full_table(),
        scenario_5_defender_takes(),
        scenario_6_late_game_no_deck(),
        scenario_7_game_over(),
        scenario_8_full_lobby_6_players(),
        scenario_9_one_on_one_final(),
        scenario_10_long_game_discard_pile(),
    ]


@benchmark(iterations=1000, warmup=100)
def standart_serialize(games: list) -> list:
    return [pickle.dumps(game) for game in games]


@benchmark(iterations=1000, warmup=100)
def modified_serialize(games: list) -> list:

    return [msgspec.msgpack.encode(game.to_dict()) for game in games]


@benchmark(iterations=1000, warmup=100)
def modified_serialize_compress(games: list) -> list:

    return [
        lz4.frame.compress(msgspec.msgpack.encode(game.to_dict()), compression_level=0)
        for game in games
    ]


@benchmark(iterations=1000, warmup=100)
def super_serialize(games: list) -> list:
    return [RedisFoolGameAdapter.encode(game) for game in games]


@benchmark(iterations=1000, warmup=100)
def super_serialize_compressed(games: list) -> list:
    return [
        lz4.frame.compress(RedisFoolGameAdapter.encode(game), compression_level=0)
        for game in games
    ]


if __name__ == "__main__":
    all_games = generate_all_scenarios()
    print(f"Сгенерировано {len(all_games)} сценариев.")
    for i, game in enumerate(all_games):
        print(
            f"  {i+1}. {game.game_id:25} | "
            f"Players: {len(game.players)} | "
            f"State: {game.current_state_name:30} | "
            f"Deck: {len(game.deck):2} | "
            f"Trump: {game.deck.trump_suit.name if game.deck.trump_suit else 'N/A'}"
        )

    one = standart_serialize(all_games)
    two = modified_serialize(all_games)
    three = modified_serialize_compress(all_games)
    four = super_serialize(all_games)
    five = super_serialize_compressed(all_games)
    print(measure_memory(all_games))
    print(measure_memory(one))
    print(measure_memory(two))
    print(measure_memory(three))
    print(measure_memory(four))
    print(measure_memory(five))
