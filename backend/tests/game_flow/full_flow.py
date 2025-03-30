import pytest
from backend.app.models.game import FoolGame
from backend.app.contracts.game_contract import PlayerInput, PlayerAction, ActionResult
from backend.app.models.card import Card, Suit, Rank

@pytest.fixture
def initialized_game():
    game = FoolGame(players_limit=2)
    
    # Добавляем двух игроков
    game.handle_input(PlayerInput(player_id=1, action=PlayerAction.JOIN))
    game.handle_input(PlayerInput(player_id=2, action=PlayerAction.JOIN))
    
    # Помечаем их готовыми
    game.handle_input(PlayerInput(player_id=1, action=PlayerAction.READY))
    game.handle_input(PlayerInput(player_id=2, action=PlayerAction.READY))
    
    return game

def test_full_game_flow(initialized_game):
    game = initialized_game
    
    # Проверяем начальное состояние
    assert game.current_state.__class__.__name__ == "DealState"
    
    # Эмулируем процесс игры
    attacker_id = 1
    defender_id = 2
    
    # Получаем карты игроков
    attacker_cards = game.players[attacker_id].cards
    defender_cards = game.players[defender_id].cards
    
    # Выбираем первую карту для атаки
    attack_card = attacker_cards[0]
    
    # Атака
    response = game.handle_input(PlayerInput(
        player_id=attacker_id,
        action=PlayerAction.ATTACK,
        attack_card=attack_card
    ))
    assert response.result == ActionResult.SUCCESS
    
    # Защита
    defend_card = next((c for c in defender_cards if c > attack_card), None)
    assert defend_card is not None, "Defender has no suitable cards"
    
    response = game.handle_input(PlayerInput(
        player_id=defender_id,
        action=PlayerAction.DEFEND,
        defend_card=defend_card
    ))
    assert response.result == ActionResult.SUCCESS
    
    # Переход в состояние завершения раунда
    assert game.current_state.__class__.__name__ == "PlayRoundWithThrowState"
    
    # Завершение раунда
    response = game.handle_input(PlayerInput(
        player_id=defender_id,
        action=PlayerAction.PASS
    ))
    assert response.result == ActionResult.SUCCESS
    
    # Проверяем переход в состояние завершения игры
    assert game.current_state.__class__.__name__ == "GameOverState"
    
    # Проверяем очистку данных
    assert len(game.table.attack_cards) == 0
    assert len(game.table.defend_cards) == 0
    for player in game.players.values():
        assert player.status.name == "NOT_READY"
        assert len(player.cards) == 0
