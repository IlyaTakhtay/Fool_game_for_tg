import pytest
from unittest.mock import Mock, MagicMock
from backend.app.states.game_over import GameOverState
from backend.app.contracts.game_contract import (
    PlayerInput,
    PlayerAction,
    StateResponse,
    ActionResult,
)
from backend.app.models.player import PlayerStatus
from unittest.mock import ANY


@pytest.fixture
def mock_game():
    game = MagicMock()
    game.players = [MagicMock(), MagicMock()]
    game.game_table = MagicMock()
    return game


class TestGameOverState:

    def test_enter_sends_ready_input(self, mock_game):
        state = GameOverState(mock_game)
        state.enter()

        mock_game.handle_input.assert_called_once_with(
            player_input=ANY  # Проверяем только тип аргумента
        )

        # Дополнительная проверка содержимого
        args, kwargs = mock_game.handle_input.call_args
        assert kwargs["player_input"].player_id == 99
        assert kwargs["player_input"].action == PlayerAction.READY

    def test_handle_input_always_returns_lobby_state(self, mock_game):
        state = GameOverState(mock_game)
        response = state.handle_input(PlayerInput(1, PlayerAction.ATTACK))

        assert response.result == ActionResult.SUCCESS
        assert response.message == "Подготавливаем новую игру"
        assert response.next_state == "LobbyState"

    def test_exit_clears_game_state(self, mock_game):
        state = GameOverState(mock_game)

        # Настраиваем игроков с картами и статусами
        mock_game.players[0].status = PlayerStatus.VICTORY
        mock_game.players[1].status = PlayerStatus.READY
        mock_game.players[0].get_cards.return_value = [MagicMock()]
        mock_game.players[1].get_cards.return_value = [MagicMock()]

        state.exit()

        # Проверяем очистку статусов
        for player in mock_game.players:
            assert player.status == PlayerStatus.UNREADY
            player.clear_hand.assert_called_once()

        # Проверяем очистку стола
        mock_game.game_table.clear_table.assert_called_once()

    def test_clear_statuses_method(self, mock_game):
        state = GameOverState(mock_game)
        mock_game.players[0].status = PlayerStatus.VICTORY
        mock_game.players[1].status = PlayerStatus.READY

        state._clear_statuses()

        for player in mock_game.players:
            assert player.status == PlayerStatus.UNREADY

    def test_clear_players_cards_method(self, mock_game):
        state = GameOverState(mock_game)
        state._clear_players_cards()

        for player in mock_game.players:
            player.clear_hand.assert_called_once()

    def test_get_allowed_actions_returns_parent_implementation(self, mock_game):
        state = GameOverState(mock_game)
        assert state.get_allowed_actions() is None
