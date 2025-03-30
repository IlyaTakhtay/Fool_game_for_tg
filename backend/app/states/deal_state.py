from __future__ import annotations
from typing import Dict, List, Any, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from backend.app.models.game import FoolGame

from backend.app.contracts.game_contract import ActionResult, PlayerAction, PlayerInput, StateResponse
from backend.app.models.player import Player, PlayerStatus
from backend.app.utils.game_interface import GameState


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
        if not self._check_win_condition():
            return StateResponse(
                ActionResult.SUCCESS,
                "Продолжаем игру",
                # чтобы определить какое условие подкидывания стоит
                f"{self.game.state_history[-1]}"
            )
        else:
            return StateResponse(
                ActionResult.GAME_OVER,
                "Игра окончена",
                "GameOverState"
        )
    def exit(self) -> None:
        """Выход из состояния раздачи"""
        # Определение новых ролей если игра продолжается
        self._update_roles()
    
    def _check_win_condition(self) -> bool:
        """Проверка условий победы. Возвращает True если игра завершена."""
        # Установка окончания участия для игроков без карт и с пустой колодой"""
        # TODO: тут чутка дублирование получается
        victors = [p for p in self.game.players if not p.get_cards() and len(self.game.deck)]
        if victors:
            for player in victors:
                player.status = PlayerStatus.VICTORY

        # Проверка на последнего с картами
        active_players = [player.status != PlayerStatus.VICTORY for player in self.game.players]
        if len(active_players) <= 1:
            True
        else: 
            return False

    def _update_roles(self) -> None:
        active_players = [p for p in self.game.players 
                        if p.status != PlayerStatus.VICTORY]
        
        if not active_players:
            return
        
        if self.game.round_defender_status == PlayerAction.DEFEND:
            # Новый атакующий - текущий защитник
            new_attacker_idx = self.game.current_defender_idx
        else:
            # Новый атакующий - следующий после защитника (в оригинальном списке)
            new_attacker_idx = (self.game.current_defender_idx + 1) % len(self.game.players)
        
        # Ищем следующего активного атакующего
        for _ in range(len(self.game.players)):
            candidate = self.game.players[new_attacker_idx]
            if candidate.status != PlayerStatus.VICTORY:
                self.game.current_attacker_id = candidate.id
                break
            new_attacker_idx = (new_attacker_idx + 1) % len(self.game.players)
        
        # Ищем следующего активного защитника
        defender_idx = (new_attacker_idx + 1) % len(self.game.players)
        for _ in range(len(self.game.players)):
            candidate = self.game.players[defender_idx]
            if candidate.status != PlayerStatus.VICTORY:
                self.game.current_defender_id = candidate.id
                break
            defender_idx = (defender_idx + 1) % len(self.game.players)




    def _deal_cards(self) -> None:
        """Логика раздачи карт"""
        # Порядок раздачи: атакующий -> другие игроки -> защищающийся
        players_order = (
            self.game.players[self.game.attacker_idx:] 
            + self.game.players[:self.game.attacker_idx]
        )
        
        # Раздача всем кроме защищающегося
        defender = next(p for p in players_order 
                       if p.id == self.game.current_defender_id)
        
        for player in players_order:
            if player == defender:
                continue
            self._fill_hand(player)
        
        # Раздача защищающемуся
        self._fill_hand(defender)

    def _fill_hand(self, player: Player) -> None:
        """Добирает карты игроку до 6 из колоды"""
        while len(player.cards) < 6 and len(self.game.deck) > 0:
            card = self.game.deck.draw()
            if card is not None:
                player.add_card(card)

    def update_player_statuses(self) -> None:
        """Сброс статусов игроков"""
        for player in self.game.players :
            if player.status == PlayerStatus.READY:
                player.status = PlayerStatus.NOT_READY
