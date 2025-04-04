import pytest
from unittest.mock import MagicMock, Mock, patch

from backend.app.contracts.game_contract import PlayerInput, PlayerAction, ActionResult, StateResponse
from backend.app.models.card import Card
from backend.app.models.game import FoolGame
from backend.app.models.player import Player, PlayerStatus
from backend.app.states.lobby_state import LobbyState


@pytest.fixture
def game_mock():
    """Фикстура для создания мока игры"""
    game = Mock(spec=FoolGame)
    game.players = []
    game.players_limit = 3  # Лимит игроков - 3
    game.deck = Mock()
    game.game_table = Mock()
    game.current_attacker_id = None
    game.current_defender_id = None
    return game


@pytest.fixture
def lobby_state(game_mock):
    """Фикстура для создания состояния лобби"""
    return LobbyState(game_mock)


def test_enter_state(lobby_state, game_mock):
    """Тест входа в состояние лобби"""
    result = lobby_state.enter()
    
    # Проверяем, что метод возвращает правильные данные
    assert "message" in result
    assert "players_count" in result
    assert result["players_count"] == 0
    
    # Проверяем, что игровые переменные сбрасываются
    game_mock.deck.generate_deck.assert_called_once()
    game_mock.game_table.clear_table.assert_called_once()
    assert game_mock.current_attacker_id is None
    assert game_mock.current_defender_id is None


def test_join_player(lobby_state, game_mock):
    """Тест присоединения игрока к лобби"""
    player_input = PlayerInput(player_id=1, action=PlayerAction.JOIN)
    response = lobby_state.handle_input(player_input)
    
    # Проверяем результат
    assert response.result == ActionResult.SUCCESS
    assert len(game_mock.players) == 1
    assert game_mock.players[0].id_ == 1


def test_join_player_already_in_lobby(lobby_state, game_mock):
    """Тест присоединения игрока, который уже в лобби"""
    # Добавляем игрока в список
    game_mock.players.append(Player(1, "Player 1"))
    
    player_input = PlayerInput(player_id=1, action=PlayerAction.JOIN)
    response = lobby_state.handle_input(player_input)
    
    # Проверяем результат
    assert response.result == ActionResult.INVALID_ACTION
    assert len(game_mock.players) == 1


def test_join_player_lobby_full(lobby_state, game_mock):
    """Тест присоединения игрока, когда лобби заполнено"""
    # Заполняем лобби
    game_mock.players = [Player(1, "Player 1"), Player(2, "Player 2"), Player(3, "Player 3")]
    
    player_input = PlayerInput(player_id=4, action=PlayerAction.JOIN)
    response = lobby_state.handle_input(player_input)
    
    # Проверяем результат
    assert response.result == ActionResult.ROOM_FULL
    assert len(game_mock.players) == 3


def test_player_ready(lobby_state, game_mock):
    """Тест установки статуса готовности игрока"""
    # Добавляем игрока в список
    game_mock.players.append(Player(1, "Player 1"))
    
    player_input = PlayerInput(player_id=1, action=PlayerAction.READY)
    response = lobby_state.handle_input(player_input)
    
    # Проверяем результат
    assert response.result == ActionResult.SUCCESS
    assert game_mock.players[0].status == PlayerStatus.READY


def test_player_ready_not_found(lobby_state, game_mock):
    """Тест установки статуса готовности для несуществующего игрока"""
    player_input = PlayerInput(player_id=999, action=PlayerAction.READY)
    response = lobby_state.handle_input(player_input)
    
    # Проверяем результат
    assert response.result == ActionResult.INVALID_ACTION
    assert "Игрок не найден" in response.message


def test_all_players_ready_start_game(lobby_state, game_mock):
    """Тест начала игры, когда все игроки готовы"""
    # Добавляем трех игроков в список
    player1 = Player(1, "Player 1")
    player1.status = PlayerStatus.READY
    player2 = Player(2, "Player 2")
    player2.status = PlayerStatus.READY
    player3 = Player(3, "Player 3")
    game_mock.players = [player1, player2, player3]
    
    # Третий игрок становится готовым
    player_input = PlayerInput(player_id=3, action=PlayerAction.READY)
    response = lobby_state.handle_input(player_input)
    
    # Проверяем результат
    assert response.result == ActionResult.SUCCESS
    assert response.next_state == "PlayRoundWithoutThrowState"
    assert "Все игроки готовы" in response.message


def test_not_all_players_ready(lobby_state, game_mock):
    """Тест, что игра не начинается, если готовы не все игроки"""
    # Добавляем трех игроков, два из которых готовы
    player1 = Player(1, "Player 1")
    player1.status = PlayerStatus.READY
    player2 = Player(2, "Player 2")
    player2.status = PlayerStatus.READY
    player3 = Player(3, "Player 3")  # Не готов
    game_mock.players = [player1, player2, player3]
    
    # Проверяем, что игра не начинается
    response = lobby_state.handle_input(PlayerInput(player_id=2, action=PlayerAction.READY))
    
    assert response.result == ActionResult.SUCCESS
    assert response.next_state is None  # Игра не должна начаться
    assert "готов к игре" in response.message


def test_player_quit(lobby_state, game_mock):
    """Тест выхода игрока из лобби"""
    # Добавляем игрока в список
    game_mock.players.append(Player(1, "Player 1"))
    
    player_input = PlayerInput(player_id=1, action=PlayerAction.QUIT)
    response = lobby_state.handle_input(player_input)
    
    # Проверяем результат
    assert response.result == ActionResult.SUCCESS
    assert len(game_mock.players) == 0
    assert "покинул игру" in response.message


def test_get_allowed_actions(lobby_state, game_mock):
    """Тест получения разрешенных действий для игроков"""
    # Добавляем трех игроков с разными статусами
    player1 = Player(1, "Player 1")
    player2 = Player(2, "Player 2")
    player2.status = PlayerStatus.READY
    player3 = Player(3, "Player 3")
    player3.status = PlayerStatus.READY
    game_mock.players = [player1, player2, player3]
    
    allowed_actions = lobby_state.get_allowed_actions()
    
    # Проверяем результат
    assert 1 in allowed_actions
    assert 2 in allowed_actions
    assert 3 in allowed_actions
    assert PlayerAction.READY in allowed_actions[1]
    assert PlayerAction.QUIT in allowed_actions[1]
    assert PlayerAction.QUIT in allowed_actions[2]
    assert PlayerAction.QUIT in allowed_actions[3]
    assert PlayerAction.READY not in allowed_actions[2]
    assert PlayerAction.READY not in allowed_actions[3]


def test_invalid_action(lobby_state, game_mock):
    """Тест обработки недопустимого действия"""
    player_input = PlayerInput(player_id=1, action=PlayerAction.ATTACK)
    response = lobby_state.handle_input(player_input)
    
    # Проверяем результат
    assert response.result == ActionResult.INVALID_ACTION
    assert "Недопустимое действие" in response.message


def test_exit_state(lobby_state, game_mock):
    """Тест выхода из состояния лобби"""
    # Создаем мок колоды с уникальными картами
    mock_deck = MagicMock()
    mock_cards = [MagicMock(spec=Card) for _ in range(36)]
    mock_deck.draw.side_effect = mock_cards
    
    # Присваиваем мок колоды игровому объекту
    game_mock.deck = mock_deck
    
    # Добавляем игроков
    player1 = Player(1, "Player 1")
    player2 = Player(2, "Player 2")
    player3 = Player(3, "Player 3")
    game_mock.players = [player1, player2, player3]
    
    # Настраиваем мок для определения первого атакующего
    with patch.object(lobby_state, '_determine_first_attacker', return_value=1):
        result = lobby_state.exit()
    
    assert "message" in result
    assert game_mock.current_attacker_id == 1
    assert game_mock.current_defender_id == 2


@pytest.mark.parametrize("player_id, expected_status", [
    (1, PlayerStatus.READY),
    (2, PlayerStatus.READY),
    (3, PlayerStatus.READY)
])
def test_multiple_players_ready(lobby_state, game_mock, player_id, expected_status):
    """Тест установки статуса готовности для нескольких игроков"""
    # Добавляем игроков
    game_mock.players = [Player(1, "Player 1"), Player(2, "Player 2"), Player(3, "Player 3")]
    
    player_input = PlayerInput(player_id=player_id, action=PlayerAction.READY)
    lobby_state.handle_input(player_input)
    
    # Находим игрока и проверяем его статус
    player = next(p for p in game_mock.players if p.id_ == player_id)
    assert player.status == expected_status
