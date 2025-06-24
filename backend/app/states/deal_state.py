from __future__ import annotations
from typing import Dict, List, Any, Optional, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from backend.app.models.game import FoolGame

from backend.app.contracts.game_contract import (
    ActionResult,
    PlayerAction,
    PlayerInput,
    StateResponse,
    StateTransition,
)
from backend.app.models.player import Player, PlayerStatus
from backend.app.utils.game_interface import GameState
from backend.app.models.card import Card, Rank, Suit

logger = logging.getLogger(__name__)


class DealState(GameState):
    """
    Состояние игры: раздача карт
    """

    def __init__(self, game: FoolGame):
        self.game: FoolGame = game

    def enter(self) -> None:
        """Возвращает True если игра завершена"""
        self._deal_cards()
        self.update_player_statuses()
        # Заглушка для инициации перехода к другому состоянию #TODO: либо убрать состояние DealState либо переписать обработку enter в классе FoolGame
        self.game.handle_input(
            player_input=PlayerInput(
                99,
                PlayerAction.READY,
            )
        )
        # TODO: обновить возвраты
        # return {
        #     "message": "Драка завершена.",
        #     "table_cards": [str(card) for card in self.game.game_table.table_cards]
        # }

    def handle_input(self, player_input: PlayerInput) -> StateResponse:
        if not self._check_win_condition():
            return StateResponse(
                ActionResult.SUCCESS,
                "Продолжаем игру",
                # чтобы определить какое условие подкидывания стоит
                f"{self.game.state_history[-1]}",
            )
        else:
            return StateResponse(
                ActionResult.GAME_OVER, "Игра окончена", "GameOverState"
            )

    def exit(self) -> None:
        """Выход из состояния раздачи"""
        # Определение новых ролей если игра продолжается
        self._update_roles()

    def get_allowed_actions(self) -> None:
        """
        Заглушка имплементации
        """
        return None

    def _check_win_condition(self) -> bool:
        """Проверка условий победы. Возвращает True если игра завершена."""
        # Установка окончания участия для игроков без карт и с пустой колодой"""
        if len(self.game.deck) == 0:
            victors = [p for p in self.game.players if len(p.get_cards()) == 0]
            if victors:
                for player in victors:
                    player.status = PlayerStatus.VICTORY
            # Проверка на последнего с картами
            active_players = [
                player
                for player in self.game.players
                if player.status != PlayerStatus.VICTORY
            ]
            if len(active_players) <= 1:
                return True
        return False

    def _update_roles(self) -> None:
        # Получаем активных игроков (без победителей)
        active_players = [
            p for p in self.game.players if p.status != PlayerStatus.VICTORY
        ]

        if not active_players:
            self.game.current_attacker_id = None
            self.game.current_defender_id = None
            return

        # Функция для поиска следующего активного игрока
        def find_next_active(start_idx: int) -> int:
            for i in range(len(self.game.players)):
                idx = (start_idx + i) % len(self.game.players)
                if self.game.players[idx].status != PlayerStatus.VICTORY:
                    return idx
            return -1  # На случай, если все игроки победили

        # Определяем нового атакующего
        if self.game.round_defender_status == PlayerAction.DEFEND:
            start_idx = self.game.current_defender_idx or 0
        else:
            start_idx = (self.game.current_defender_idx + 1) % len(self.game.players)

        new_attacker_idx = find_next_active(start_idx)

        # Определяем нового защитника (следующий после атакующего)
        new_defender_idx = find_next_active(
            (new_attacker_idx + 1) % len(self.game.players)
        )

        # Обновляем ID текущих игроков
        if new_attacker_idx != -1:
            self.game.current_attacker_id = self.game.players[new_attacker_idx].id_

        if new_defender_idx != -1:
            self.game.current_defender_id = self.game.players[new_defender_idx].id_

    def _deal_cards(self) -> None:
        """Логика раздачи карт"""
        # Порядок раздачи: атакующий -> другие игроки -> защищающийся
        players_order = (
            self.game.players[self.game.current_attacker_idx :]
            + self.game.players[: self.game.current_attacker_idx]
        )

        # Раздача всем кроме защищающегося
        defender = self.game.players[self.game.current_defender_idx]

        for player in players_order:
            if player == defender:
                continue
            self._fill_hand(player)

        # Раздача защищающемуся
        self._fill_hand(defender)

    def _fill_hand(self, player: Player) -> None:
        """Добирает карты игроку до 6 из колоды"""
        while len(player.get_cards()) < 6 and len(self.game.deck) > 0:
            card = self.game.deck.draw()
            if card is not None:
                player.add_card(card)

    def update_player_statuses(self) -> None:
        """Сброс статусов игроков"""
        for player in self.game.players:
            if player.status == PlayerStatus.READY:
                player.status = PlayerStatus.UNREADY
