from __future__ import annotations
from backend.app.contracts.game_contract import ActionResult, PlayerAction, PlayerInput, StateResponse
from backend.app.models.player import PlayerStatus
from backend.app.utils.game_interface import GameState
from typing import Dict, List, Any, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from backend.app.models.game import FoolGame

class GameOverState(GameState):
    pass
    #TODO по идее просто крафтим штуку кторая очистит все левые поля и переключит в lobby_state вместе со всеми игроками
    """
    Состояние игры: Завершение матча
    """
    def __init__(self, game: FoolGame):
        self.game: FoolGame = game
        
    def enter(self) -> None:
        """Отправляем заглушку"""
        # Заглушка для инициации перехода к другому состоянию #TODO: либо убрать состояние DealState либо переписать обработку enter в классе FoolGame
        self.game.handle_input(player_input=PlayerInput(
            99,
            PlayerAction.READY,
        ))
        #TODO: обновить возвраты
        # return {
        #     "message": "Драка завершена.",
        #     "table_cards": [str(card) for card in self.game.game_table.table_cards]
        # }
    def handle_input(self, player_input: PlayerInput) -> StateResponse:
            return StateResponse(
                ActionResult.SUCCESS,
                "Подготавливаем новую игру",
                "LobbyState"
            )
    def exit(self) -> None:
        """Выход из состояния раздачи"""
        # Определение новых ролей если игра продолжается
        self._clear_statuses()
        self.game.game_table.clear_table()
        self._clear_players_cards()
    
    def _clear_statuses(self) -> None:
        """Очистка ролей игроков"""
        for player in self.game.players:
            player.status = PlayerStatus.NOT_READY

    def _clear_players_cards(self) -> None:
        for player in self.game.players:
            player.clear_hand()

    def get_allowed_actions(self):
        return super().get_allowed_actions()

