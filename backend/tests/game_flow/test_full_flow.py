import random
import uuid
import pytest
import logging

from backend.app.models.game import FoolGame
from backend.app.contracts.game_contract import PlayerInput, PlayerAction, ActionResult
from backend.app.models.card import Card, Suit, Rank, TrumpCard
from backend.app.models.player import Player, PlayerStatus



@pytest.fixture
def initialized_game():
    game = FoolGame(uuid.uuid4, players_limit=2)

    # Добавляем двух игроков
    game.handle_input(PlayerInput(player_id=1, action=PlayerAction.JOIN))
    game.handle_input(PlayerInput(player_id=2, action=PlayerAction.JOIN))

    # Помечаем их готовыми
    print(game.handle_input(PlayerInput(player_id=1, action=PlayerAction.READY)))
    print(game.handle_input(PlayerInput(player_id=2, action=PlayerAction.READY)))

    return game


def find_defend_card(player_cards: Card, attack_card: Card) -> Card | None:
    for c in player_cards:
        try:
            if c > attack_card:
                return c
        except TypeError:
            continue
    return None


def synthesized_defend_card_from_deck(game: FoolGame, attack_card) -> Card | None:
    for c in game.deck._cards:
        try:
            if c > attack_card:
                defender: Player = game.players[game.current_defender_idx]
                defender_card = random.sample(defender.get_cards(), 1)[0]
                defender.remove_card(defender_card)
                defender.add_card(c)
                game.deck._cards.insert(-1, defender_card)
                return c
        except TypeError:
            continue
    return None


def test_game_flow_until_card_draw(initialized_game: FoolGame):
    game: FoolGame = initialized_game

    # проверяем, что инициализация прошла успешно
    assert game._current_state.__class__.__name__ == "PlayRoundWithoutThrowState"

    # Эмулируем процесс игры
    starter_attacker_id = game.current_attacker_id
    starter_defender_id = game.current_defender_id

    # Получаем карты игроков
    attacker_cards = game.players[game.current_attacker_idx].get_cards()
    defender_cards = game.players[game.current_defender_idx].get_cards()

    # Выбираем первую карту для атаки
    attack_card = random.sample(attacker_cards, 1)[0]

    # Атака
    response = game.handle_input(
        PlayerInput(
            player_id=game.current_attacker_id,
            action=PlayerAction.ATTACK,
            attack_card=attack_card,
        )
    )
    assert response.result == ActionResult.SUCCESS

    logger.debug(game.players[game.current_attacker_idx].get_cards())
    # Защита
    defend_card = find_defend_card(defender_cards, attack_card)
    if defend_card is None:
        defend_card = synthesized_defend_card_from_deck(game, attack_card)

    logger.debug(attack_card)
    logger.debug(defend_card)

    if defend_card is None:
        response = game.handle_input(
            PlayerInput(player_id=game.current_defender_id, action=PlayerAction.CLOLECT)
        )
        # assert len(game.players[game.current_defender_idx].get_cards()) == 7
    else:
        response = game.handle_input(
            PlayerInput(
                player_id=game.current_defender_id,
                action=PlayerAction.DEFEND,
                attack_card=attack_card,
                defend_card=defend_card,
            )
        )
        # assert len(game.players[game.current_defender_idx].get_cards()) == 6
    assert response.result == ActionResult.SUCCESS

    # Завершение раунда
    response = game.handle_input(
        PlayerInput(player_id=game.current_attacker_id, action=PlayerAction.PASS)
    )
    assert response.exit_info["message"] == "Драка завершена."

    # Переход в состояние дальнешей игры
    assert game._current_state.__class__.__name__ == "PlayRoundWithoutThrowState"

    assert starter_attacker_id == game.current_defender_id
    assert starter_defender_id == game.current_attacker_id
    assert len(game.players[game.current_attacker_idx].get_cards()) == 6
    assert len(game.players[game.current_defender_idx].get_cards()) == 6

    game.players[game.current_attacker_idx].clear_hand()

    assert len(game.players[game.current_attacker_idx].get_cards()) == 0

    game.game_table.table_cards = [{"attack_card": Card(Rank.SEVEN, Suit.HEARTS)}]

    synthesized_defend_card = Card(Rank.ACE, Suit.HEARTS)

    if (
        synthesized_defend_card
        not in game.players[game.current_defender_idx].get_cards()
    ):
        game.players[game.current_defender_idx].add_card(synthesized_defend_card)
    assert len(game.players[game.current_attacker_idx].get_cards()) != 1

    response = game.handle_input(
        PlayerInput(
            player_id=game.current_defender_id,
            action=PlayerAction.DEFEND,
            attack_card=game.game_table.table_cards[0]["attack_card"],
            defend_card=synthesized_defend_card,
        )
    )

    logger.debug(response)
    assert response.result == ActionResult.SUCCESS
    response = game.handle_input(
        PlayerInput(player_id=game.current_attacker_id, action=PlayerAction.PASS)
    )
    logger.debug(response)

    response.new_state == "PlayRoundWithoutThrowState"
    assert len(game.players[game.current_attacker_idx].get_cards()) == 6
    assert len(game.players[game.current_defender_idx].get_cards()) == 6
    assert game._current_state.__class__.__name__ == "PlayRoundWithoutThrowState"
    assert starter_attacker_id == game.current_attacker_id
    assert starter_defender_id == game.current_defender_id
    logger.debug(response)


def test_game_flow_until_end_cond_demo(initialized_game: FoolGame):
    game: FoolGame = initialized_game

    # Проверяем начальное состояние
    assert game._current_state.__class__.__name__ == "PlayRoundWithoutThrowState"

    # Получаем карты игроков
    attacker_cards = game.players[game.current_attacker_idx].get_cards()
    defender_cards = game.players[game.current_defender_idx].get_cards()

    # синтезируем карту защиты
    synthesized_defend_card = TrumpCard(Rank.ACE, game.deck.trump_suit)

    # Выбираем первую карту для атаки
    attack_card = random.sample(attacker_cards, 1)[0]

    if attack_card == synthesized_defend_card:
        attack_player: Player = game.players[game.current_attacker_idx]
        attack_player.get_cards().remove(attack_card)
        attack_player.add_card(random.sample(defender_cards, 1)[0])
    else:
        rem_card = random.sample(defender_cards, 1)[0]
        defend_player: Player = game.players[game.current_defender_idx]
        defend_player.remove_card(rem_card)
        game.deck._cards.insert(-1, rem_card)
        defend_player.remove_card(random.sample(defender_cards, 1)[0])
        if synthesized_defend_card not in defend_player.get_cards():
            defend_player.add_card(synthesized_defend_card)

    # Атака
    response = game.handle_input(
        PlayerInput(
            player_id=game.current_attacker_id,
            action=PlayerAction.ATTACK,
            attack_card=attack_card,
        )
    )
    assert response.result == ActionResult.SUCCESS
    logger.debug(game.players[game.current_attacker_idx].get_cards())

    response = game.handle_input(
        PlayerInput(
            player_id=game.current_defender_id,
            action=PlayerAction.DEFEND,
            attack_card=attack_card,
            defend_card=synthesized_defend_card,
        )
    )
    assert response.result == ActionResult.SUCCESS

    # Завершение раунда
    response = game.handle_input(
        PlayerInput(player_id=game.current_attacker_id, action=PlayerAction.PASS)
    )
    assert response.exit_info["message"] == "Драка завершена."

    # Переход в состояние дальнешей игры
    assert game._current_state.__class__.__name__ == "PlayRoundWithoutThrowState"

    # очишаем руку игрока атаки и добавляем карту для защиты на стол
    game.players[game.current_attacker_idx].clear_hand()
    assert len(game.players[game.current_attacker_idx].get_cards()) == 0
    if game.deck.trump_suit == Suit.HEARTS:
        game.game_table.table_cards = [
            {"attack_card": TrumpCard(Rank.SEVEN, Suit.HEARTS)}
        ]
    else:
        game.game_table.table_cards = [{"attack_card": Card(Rank.SEVEN, Suit.HEARTS)}]

    # Делаем карту защитнику, которой он 100% отобьется, чтобы симулировать проигрыш при отбивке
    if game.deck.trump_suit == Suit.HEARTS:
        synthesized_defend_card = TrumpCard(Rank.KING, Suit.HEARTS)
    else:
        synthesized_defend_card = Card(Rank.KING, Suit.HEARTS)
    # Добавляем в руку игроку карту, чтобы когда будет проверка в игре, она провалидировалась
    if (
        synthesized_defend_card
        not in game.players[game.current_defender_idx].get_cards()
    ):
        game.players[game.current_defender_idx].add_card(synthesized_defend_card)
    # чистим ассеты
    game.deck._cards.clear()
    assert len(game.deck._cards) == 0
    assert len(game.players[game.current_attacker_idx].get_cards()) == 0

    response = game.handle_input(
        PlayerInput(
            player_id=game.current_defender_id,
            action=PlayerAction.DEFEND,
            attack_card=game.game_table.table_cards[0]["attack_card"],
            defend_card=synthesized_defend_card,
        )
    )
    logger.debug(response)

    response == ActionResult.SUCCESS
    response = game.handle_input(
        PlayerInput(player_id=game.current_attacker_id, action=PlayerAction.PASS)
    )

    assert len(game.players[0].get_cards()) == 0
    assert len(game.players[1].get_cards()) == 0
    assert game.players[0].status == PlayerStatus.UNREADY
    assert game.players[1].status == PlayerStatus.UNREADY

    assert response.new_state == "LobbyState"
    logger.debug(response)
