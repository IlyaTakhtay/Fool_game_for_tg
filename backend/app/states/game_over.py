from __future__ import annotations
from backend.app.contracts.game_contract import (
    ActionResult,
    PlayerAction,
    PlayerInput,
    StateResponse,
)
from backend.app.models.player import PlayerStatus
from backend.app.utils.game_interface import GameState
from typing import Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.models.game import FoolGame
    from backend.app.models.player import Player


class GameOverState(GameState):
    """
    Состояние игры: Завершение матча
    """

    def __init__(self, game: FoolGame):
        self.game = game
        self.winner_id: str | None = None
        self.loser_ids: List[str] = []

    def enter(self) -> Dict[str, Any]:
        """Определяет победителя и проигравших и возвращает информацию."""
        
        # Находим игрока, у которого не осталось карт
        winner: Player | None = next(
            (p for p in self.game.players if not p.get_cards()), None
        )

        if winner:
            self.winner_id = winner.id_
            self.loser_ids = [p.id_ for p in self.game.players if p.id_ != winner.id_]
            message = f"Игра окончена! Победитель: {winner.name}."
        else:
            # Случай "ничьи", если у нескольких игроков одновременно кончились карты,
            # или если победитель не определен по какой-то причине.
            self.loser_ids = [p.id_ for p in self.game.players]
            message = "Игра окончена! Победителя нет."
            
        return {
            "message": message,
            "winner_id": self.winner_id,
            "loser_ids": self.loser_ids,
        }

    def exit(self) -> Dict[str, Any]:
        return {"message": "Выход из экрана окончания игры."}

    def handle_input(self, player_input) -> None:
        # В этом состоянии нет действий от игроков
        return None

    def get_allowed_actions(self) -> Dict[str, list]:
        # В этом состоянии нет разрешенных действий
        return {p.id_: [] for p in self.game.players}

    def get_state_info(self) -> Dict[str, Any]:
        return {
            "message": "Игра окончена",
            "winner_id": self.winner_id,
            "loser_ids": self.loser_ids,
        }

    def _clear_statuses(self) -> None:
        """Очистка ролей игроков"""
        for player in self.game.players:
            player.status = PlayerStatus.UNREADY

    def _clear_players_cards(self) -> None:
        for player in self.game.players:
            player.clear_hand()
