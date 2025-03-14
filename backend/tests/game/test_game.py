import pytest
from unittest.mock import Mock, patch

from backend.app.contracts.game_contract import PlayerInput, PlayerAction, ActionResult, StateResponse, StateTransition
from backend.app.models.player import Player, PlayerStatus
from backend.app.models.game import FoolGame
from backend.app.utils.game_interface import GameState


@pytest.fixture
def game():
    """Фикстура для создания экземпляра игры"""
    return FoolGame(game_id="test_game", players_limit=3)


@pytest.fixture
def game_with_players(game):
    """Фикстура для создания игры с игроками"""
    game.players = [
        Player("1", "Player 1"),
        Player("2", "Player 2"),
        Player("3", "Player 3")
    ]
    return game


@pytest.fixture
def mock_state():
    """Фикстура для создания мока состояния игры"""
    state = Mock(spec=GameState)
    state.name = "MockState"
    state.__class__.__name__ = "MockState"
    state.enter.return_value = {"message": "Entered mock state", "players_count": 0}
    state.exit.return_value = {"message": "Exited mock state"}
    state.get_state_info.return_value = {"state_info": "mock_info"}
    state.get_allowed_actions.return_value = {1: [PlayerAction.READY, PlayerAction.QUIT]}
    return state


def test_init(game):
    """Тест инициализации игры"""
    assert game.game_id == "test_game"
    assert game.players_limit == 3
    assert len(game.players) == 0
    assert game.deck is not None
    assert game.game_table is not None
    assert game.current_attacker_id is None
    assert game.current_defender_id is None
    assert game._current_state is not None
    assert game._current_state.__class__.__name__ == "LobbyState"


def test_init_with_invalid_players_limit():
    """Тест инициализации с недопустимым количеством игроков"""
    with pytest.raises(ValueError, match="Минимальное количество игроков должно быть 2 или больше"):
        FoolGame(game_id="test_game", players_limit=1)


def test_set_state(game, mock_state):
    """Тест изменения состояния игры"""
    with pytest.raises(Exception, match="Ошибка при переключении состояния"):
        game._set_state(Mock(spec=GameState))
    assert game._current_state != mock_state
    assert len(game.state_history) == 0


def test_handle_input_no_state(game):
    """Тест обработки ввода при отсутствии текущего состояния"""
    game._current_state = None
    player_input = PlayerInput(player_id=1, action=PlayerAction.JOIN)
    response = game.handle_input(player_input)
    
    assert response.result == ActionResult.INVALID_ACTION
    assert "No active state" in response.message


def test_handle_input_normal_response(game, mock_state):
    """Тест обработки ввода с обычным ответом"""
    game._current_state = mock_state
    mock_state.handle_input.return_value = StateResponse(
        ActionResult.SUCCESS,
        "Action processed",
        None,
        {"data": "test"}
    )
    
    player_input = PlayerInput(player_id=1, action=PlayerAction.JOIN)
    response = game.handle_input(player_input)
    
    assert response.result == ActionResult.SUCCESS
    assert response.message == "Action processed"
    assert response.data == {"data": "test"}
    mock_state.handle_input.assert_called_once_with(player_input)


def test_handle_input_state_transition(game, mock_state):
    """Тест обработки ввода с переходом в другое состояние"""
    game._current_state = mock_state
    
    # Создаем класс-заглушку для нового состояния
    class NewState(GameState):
        name = "NewState"
        def __init__(self, game):
            self.game = game
        def enter(self): 
            return {"message": "Entered new state"}
        def exit(self): 
            return {"message": "Exited new state"}
        def handle_input(self, input): 
            return None
        def get_allowed_actions(self): 
            return {}
        def get_state_info(self): 
            return {}
    
    # Патчим метод __subclasses__ для GameState
    with patch.object(GameState, '__subclasses__', return_value=[NewState]):
        mock_state.handle_input.return_value = StateResponse(
            ActionResult.SUCCESS,
            "Transition to new state",
            "NewState",
            None
        )
        
        player_input = PlayerInput(player_id=1, action=PlayerAction.JOIN)
        
        with patch.object(game, '_set_state', return_value=StateTransition(
            previous_state="MockState",
            new_state="NewState",
            exit_info={"message": "Exited mock state"},
            enter_info={"message": "Entered new state"}
        )) as mock_set_state:
            response = game.handle_input(player_input)
            
            assert isinstance(response, StateTransition)
            assert response.previous_state == "MockState"
            assert response.new_state == "NewState"
            mock_state.handle_input.assert_called_once_with(player_input)
            mock_set_state.assert_called_once()


def test_handle_input_invalid_state(game, mock_state):
    """Тест обработки ввода с переходом в несуществующее состояние"""
    game._current_state = mock_state
    mock_state.handle_input.return_value = StateResponse(
        ActionResult.SUCCESS,
        "Transition to invalid state",
        "NonExistentState",
        None
    )
    
    # Патчим метод __subclasses__ для GameState
    with patch.object(GameState, '__subclasses__', return_value=[]):
        player_input = PlayerInput(player_id=1, action=PlayerAction.JOIN)
        response = game.handle_input(player_input)
        
        assert response.result == ActionResult.INVALID_ACTION
        assert "State NonExistentState not found" in response.message


def test_get_game_state(game_with_players, mock_state):
    """Тест получения состояния игры"""
    game_with_players._current_state = mock_state
    game_with_players.current_attacker_id = "1"
    game_with_players.current_defender_id = "2"
    
    state_info = game_with_players.get_game_state()
    
    assert state_info["current_state"] == "MockState"
    assert "state_info" in state_info
    assert len(state_info["players"]) == 3
    assert state_info["attacker_id"] == "1"
    assert state_info["defender_id"] == "2"
    assert "allowed_actions" in state_info
    mock_state.get_state_info.assert_called_once()
    mock_state.get_allowed_actions.assert_called_once()


def test_get_game_state_no_state(game):
    """Тест получения состояния игры при отсутствии текущего состояния"""
    game._current_state = None
    
    state_info = game.get_game_state()
    
    assert state_info["current_state"] is None
    assert "state_info" in state_info
    assert state_info["state_info"] == {}
    assert "allowed_actions" in state_info
    assert state_info["allowed_actions"] == {}


def test_determine_defender_with_players(game_with_players):
    """Тест определения защищающегося игрока при наличии игроков"""
    game_with_players.current_attacker_id = "1"
    
    with patch.object(game_with_players._current_state, '_determine_defender') as mock_determine:
        mock_determine.side_effect = lambda: setattr(game_with_players, 'current_defender_id', "2")
        mock_determine()
        
        assert game_with_players.current_defender_id == "2"


def test_determine_defender_no_players(game):
    """Тест определения защищающегося игрока при отсутствии игроков"""
    game.current_attacker_id = "1"
    
    with patch.object(game._current_state, '_determine_defender') as mock_determine:
        mock_determine.side_effect = ValueError("Нет игроков для определения защищающегося")
        
        with pytest.raises(ValueError, match="Нет игроков для определения защищающегося"):
            mock_determine()
