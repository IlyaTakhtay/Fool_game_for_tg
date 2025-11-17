from __future__ import annotations
from backend.src.game.contracts.game_contract import (
    ActionResult,
    PlayerAction,
    PlayerInput,
    StateResponse,
)
from backend.src.game.models.player import PlayerStatus
from backend.src.game.utils.game_interface import GameState
from typing import Dict, List, Any, Optional, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from backend.src.game.models.game import FoolGame
    from backend.src.game.models.player import Player

logger = logging.getLogger(__name__)


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

        if self.game.loser_ids:
            self.loser_ids = self.game.loser_ids
            self.game.loser_ids = None  # Очищаем временное поле
        else:
            # Стандартная логика определения победителя и проигравших
            winner: Player | None = next(
                (p for p in self.game.players if not p.get_cards()), None
            )

            if winner:
                self.winner_id = winner.id_
                self.loser_ids = [p.id_ for p in self.game.players if p.id_ != winner.id_]
            else:
                self.loser_ids = [p.id_ for p in self.game.players]

        # Формируем сообщение
        if self.winner_id:
            winner_player = self.game.get_player_by_id(self.winner_id)
            winner_name = winner_player.name if winner_player else "Неизвестный"
            message = f"Игра окончена! Победитель: {winner_name}."
        elif self.loser_ids:
            message = f"Игра окончена! Проигравший: {', '.join(self.loser_ids)}."
        else:
            message = "Игра окончена! Победителя нет."

        return {
            "message": message,
            "winner_id": self.winner_id,
            "loser_ids": self.loser_ids,
        }

    def exit(self) -> Dict[str, Any]:
        return {"message": "Выход из экрана окончания игры."}

    def handle_input(self, player_input) -> None:
        """
        При любой попытке действия в законченной игре возвращает
        информативный ответ о том, что действие невозможно.
        """
        if player_input.action == PlayerAction.QUIT:
            self.game.players = [p for p in self.game.players if p.id_ != player_input.player_id]
            return StateResponse(
                ActionResult.SUCCESS,
                f"Игрок {player_input.player_id} покинул игру.",
            )

        return StateResponse(
            result=ActionResult.INVALID_ACTION,
            message="Игра уже окончена. Новые действия невозможны.",
        )

    def get_allowed_actions(self) -> Dict[str, list]:
        # В этом состоянии разрешено только действие QUIT
        return {p.id_: [PlayerAction.QUIT.name] for p in self.game.players}

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
