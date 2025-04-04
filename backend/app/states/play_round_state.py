from __future__ import annotations
import logging
from typing import Dict, List, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from backend.app.models.game import FoolGame

from backend.app.utils.logger import setup_logger
from backend.app.models.card import Card
from backend.app.utils.game_interface import GameState
from backend.app.models.player import Player, PlayerStatus
from backend.app.contracts.game_contract import PlayerInput, PlayerAction, ActionResult, StateResponse, StateTransition

logger = setup_logger(__name__, log_file="logs/debug.log", level=logging.DEBUG)

class ExtraThrowActionMixin:
    def _extra_throw_action (self, player_input) -> ActionResult:
        if player_input.action == PlayerAction.PASS and player_input.player_id == self.game.current_attacker_id:
            # Пока защищающийся игрок не нажал COLLECT или не покрыл все карты, отправляем INVALID ACTION 
            if not self._is_all_cards_defended() or self.round_defender_status == PlayerAction.COLLECT:
                return StateResponse(
                    ActionResult.INVALID_ACTION,
                    "Нельзя пасовать, пока защищающийся не отбил все карты или не пасанул сам",
                )
            else:
                #TODO: сделать так, чтобы это было только ПРИ ИГРЕ С ПОДБРАСЫВАНИЕМ
                sorted_players: List[Player] = list(
                    self.game.players[self.game.current_defender_idx + 1:] +
                    self.game.players[:self.game.current_defender_idx]
                )
                next_attacker: Player = next(
                    (p for p in sorted_players 
                    if p.status == PlayerStatus.READY 
                    and p.status != PlayerStatus.VICTORY),
                    None
                )
                if next_attacker:
                    self.game.current_attacker_idx = (self.game.current_attacker_idx + 1) % len(self.game.players)
                    self.game.current_attacker_id = next_attacker
                    return StateResponse(
                        ActionResult.SUCCESS,
                        f"Ход игрока {player_input.player_id} пропущен. Ход переходит игроку {next_attacker.name}"
                    )
                else:
                    return StateResponse(
                        result = ActionResult.SUCCESS,
                        message = f"Последний закончил ход игрок {player_input.player_id}",
                        next_state = "DealState",
                        data={"table":self.game.game_table.table_cards}
                    )


    
class PlayRoundWithoutThrowState(GameState):
    """Состояние проигрыша раунда в игре Дурак, для игры с подбрасыванием"""
    
    def __init__(self, game: FoolGame) -> None:
        self.game: FoolGame = game
 

    def enter(self) -> Dict[str, Any]:
        """
        Инициализирует состояние атаки
        
        Returns:
            Dict[str, Any]: Информация о входе в состояние атаки
        """
        
        # Очищаем игровой стол перед новым раундом
        self.game.game_table.clear_table()
        
        return {
            "message": f"Ход игрока {self.game.current_attacker_id}. Выберите карту для атаки.",
            "attacker_id": self.game.current_attacker_id,
            "defender_id": self.game.current_defender_id,
            "table_cards": []
        }
    

    def exit(self) -> Dict[str, Any]:
        """
        Вызывается при выходе из состояния атаки
        
        Returns:
            Dict[str, Any]: Информация о результатах состояния
        """
        if self.game.round_defender_status == PlayerAction.DEFEND:
            # TODO: убрать константу
            self.game.game_table.slots = 6
        
        # Отдаем в руку карты со стола игроку, который не отбился
        if self.game.round_defender_status == PlayerAction.COLLECT:
            for pair in self.game.game_table.table_cards:
                for card in pair.items():
                    pl: Player = self.game.players[self.game.current_defender_idx]
                    if pl:
                        pl.add_card(card)
        logging.debug(f"current defender status is{self.game.round_defender_status}")
        # self.game.game_table.clear_table()
        return {
            "message": "Драка завершена.",
            "table_cards": [str(card) for card in self.game.game_table.table_cards]
        }
    

    def handle_input(self, player_input: PlayerInput) -> StateResponse:
        """
        Обрабатывает ввод игрока в состоянии атаки
        
        Args:
            player_input: Входные данные об игроке
            
        Returns:
            StateResponse: Результат обработки ввода
        """
        # Обработка выхода игрока
        if player_input.action == PlayerAction.QUIT:
            return self._handle_player_quit_action(player_input)
            
        
        # Проверяем, что ход принадлежит атакующему или защищающемуся игроку
        if player_input.player_id != self.game.current_attacker_id and player_input.player_id != self.game.current_defender_id:
            logger
            return StateResponse(
                ActionResult.NOT_YOUR_TURN,
                "Сейчас не ваш ход."
            )
        
        # Обработка атаки
        if player_input.action == PlayerAction.ATTACK and player_input.player_id == self.game.current_attacker_id:
            state: StateResponse = self._check_attack_rules(player_input)
            if state == ActionResult.SUCCESS:
                #TODO: сделать так, чтобы это было только ПРИ ИГРЕ С ПОДБРАСЫВАНИЕМ
                for player in self.game.players:
                    if player.status == PlayerStatus.READY:
                        player.status = PlayerStatus.NOT_READY
            return state
        
        # Обработка защиты 
        if player_input.action == PlayerAction.DEFEND and player_input.player_id == self.game.current_defender_id:
            action: PlayerAction =self._check_defend_rules(player_input)
            if action == ActionResult.SUCCESS:
                defender:Player = self.game.players[self.game.current_defender_idx]
                if not self._is_defender_able_to_beat_more(defender_cards=defender.get_cards()):
                    self.game.round_defender_status = PlayerAction.DEFEND
                    return StateResponse(
                        ActionResult.SUCCESS,
                        "Игрок отбил все карты и больше не может отбивать.",
                        "DealState",
                        {
                            "defender_id": self.game.current_defender_id,
                            "defend_card": str(player_input.defend_card),
                            "table_cards": [str(card) for card in self.game.game_table.table_cards]
                        }
                    )
            return action
        
        # Обработка паса (пропуска хода) атакующим
        if player_input.action == PlayerAction.PASS and player_input.player_id == self.game.current_attacker_id:
            # Пока защищающийся игрок не нажал COLLECT или не покрыл все карты, шлем INVALID ACTION 
            if not self._is_all_cards_defended() or self.game.round_defender_status == PlayerAction.COLLECT:
                return StateResponse(
                    ActionResult.INVALID_ACTION,
                    "Нельзя пасовать, пока защищающийся не отбил все карт ыили не пасанул сам",
                )
            else:
                return self._extra_throw_action(player_input=player_input)
        
        # Обработка сбора карт защищающимся
        if player_input.action == PlayerAction.COLLECT and player_input.player_id == self.game.current_defender_id:
            try:
                defender:Player = self.game.players[self.game.current_defender_idx]
            except (TypeError, IndexError):
                return StateResponse(
                    ActionResult.INTERNAL_ERROR,
                    "Ошибка при получении защищающегося игрока"
                )
            if defender.status != PlayerStatus.READY:
                defender.status = PlayerStatus.READY
                self.game.round_defender_status = PlayerAction.COLLECT
                return StateResponse(
                    ActionResult.SUCCESS,
                    f"Игрок {defender.name} не может отбить и забирает карты."
                )
            else:
                return StateResponse(
                    ActionResult.INVALID_ACTION,
                    "Статус взятия карт уже установлен."
                )
        
        # Если действие не распознано
        return StateResponse(
            ActionResult.INVALID_ACTION,
            "Действие не распознано."
        )


    def _extra_throw_action(self, player_input: PlayerInput) -> StateResponse:
        return StateResponse(
                        result = ActionResult.SUCCESS,
                        message = f"Последний закончил ход игрок {player_input.player_id}",
                        next_state = "DealState",
                        data={"table":self.game.game_table.table_cards}
                    )


    def _check_attack_rules(self, player_input: PlayerInput) -> StateResponse:
        # Проверка наличия карты для атаки
        if not player_input.attack_card:
            return StateResponse(
                ActionResult.CARD_REQUIRED,
                "Необходимо выбрать карту для атаки."
            )
        
        try:
            attacker: Player = self.game.players[self.game.current_attacker_idx]
        except (TypeError, IndexError):
            attacker = None
        if not attacker or player_input.attack_card not in attacker.get_cards():
            return StateResponse(
                ActionResult.INVALID_CARD,
                "У вас нет такой карты."
            )
        
        result = self.game.game_table.throw_card(player_input.attack_card)
        
        # Проверяем правила подкидывания (если стол не пуст)
        if self.game.game_table.table_cards and result["status"] == "failed":
            if result["message"] == "no free slots":
                return StateResponse(
                    ActionResult.TABLE_FULL,
                    "Стол полный"
                )
            if result["message"] == "wrong rank":
                return StateResponse(
                    ActionResult.WRONG_CARD,
                    "Эту карту нельзя подкинуть. Можно подкидывать только карты тех же достоинств, что уже есть на столе."
                )
        
        # Проверка на то, что у игрока достаточно карт для защиты
        try:
            defender:Player = self.game.players[self.game.current_defender_idx]
        except (TypeError, IndexError):
            defender = None
        if defender and not self._is_defender_able_to_beat_more(defender_cards=defender.get_cards()):
            return StateResponse(
                ActionResult.TABLE_FULL,
                "У защищающегося недостаточно карт для защиты ещё одной"
            )

        # Убираем карту у игрока из руки, потому что атака прошла успешно
        attacker.remove_card(player_input.attack_card)
        
        return StateResponse(
            ActionResult.SUCCESS,
            f"Игрок {player_input.player_id} атакует картой {player_input.attack_card}.",
            None,
            {
                "attacker_id": self.game.current_attacker_id,
                "defender_id": self.game.current_defender_id,
                "attack_card": str(player_input.attack_card),
                "table_cards": [str(card) for card in self.game.game_table.table_cards]
            }
        )


    def _check_defend_rules(self, player_input: PlayerInput) -> StateResponse:
    # Проверка наличия карты для защиты
        if not player_input.defend_card:
            return StateResponse(
                ActionResult.CARD_REQUIRED,
                "Необходимо выбрать карту для защиты."
            )
        try:
            defender: Player = self.game.players[self.game.current_defender_idx]
        except (TypeError, IndexError):
            return StateResponse(
               ActionResult.INTERNAL_ERROR,
               "Не найден игрок для защиты"
            )
        # Проверяем, что карта есть у игрока
        if not defender or player_input.defend_card not in defender.get_cards():
            return StateResponse(
                ActionResult.INVALID_CARD,
                "У вас нет такой карты."
            )
        
        # Логика защиты (cover card)
        try:
            if not self.game.game_table.cover_card(player_input.attack_card, player_input.defend_card):
                return StateResponse(
                    ActionResult.INVALID_CARD,
                    "Этой картой нельзя покрыть карту на столе",
                    None,
                    {"attack_card":player_input.attack_card, "defend_card":player_input.defend_card}
                )
        except ValueError:
            return StateResponse(
                ActionResult.INVALID_CARD,
                "Ошибка с картой на столе",
            )

        defender.remove_card(player_input.defend_card)

        return StateResponse(
            ActionResult.SUCCESS,
            f"Игрок {player_input.player_id} защищается картой {player_input.defend_card}.",
            None,
            {
                "defender_id": self.game.current_defender_id,
                "defend_card": str(player_input.defend_card),
                "table_cards": [str(card) for card in self.game.game_table.table_cards]
            }
        )


    def _is_defender_able_to_beat_more(self, defender_cards: list[Card]) -> bool: #TODO вообще здесь нужно добавить проверку на лимиты стола по идее. Я так понял нигде с ними то особо и не работаю
        """
        Проверяет, может ли защищающийся игрок отбить еще одну карту на столе
        
        Returns:
            bool: True, если может отбить ещё, иначе False
        """
        if len(self.game.game_table.table_cards) == 0:
            return True
        elif len(defender_cards) <= len([card["attack_card"] for card in self.game.game_table.table_cards if card["defend_card"] is None]):
            return False
        else:
            return True
    

    def _handle_player_quit_action(self, player_input: PlayerInput) -> StateResponse:
            if pl:= self.game.get_player_by_id(player_input.player_id):
                pl.status = PlayerStatus.LEAVED
    
                return StateResponse(
                    ActionResult.SUCCESS,
                    f"Игрок {player_input.player_id} покинул игру. Игра завершена.",
                    "GameOverState",
                    {"players_count": len(self.game.players)}
                )
            else:
                return StateResponse(
                    ActionResult.INVALID_ACTION,
                    f"Игрок {player_input.player_id} не найден."
                )

    
    def _is_all_cards_defended(self) -> bool:
        """
        Проверяет, все ли карты на столе отбиты
        
        Returns:
            bool: True, если все карты отбиты, иначе False
        """
        if not all(card.get("defend_card") for card in self.game.game_table.table_cards):
            return False
        self.game.round_defender_status = PlayerAction.DEFEND
        return True
    
    def get_allowed_actions(self) -> Dict[int, List[PlayerAction]]:
        """
        Возвращает список разрешенных действий для каждого игрока
        
        Returns:
            Dict[int, List[PlayerAction]]: Словарь {id_игрока: [разрешенные_действия]}
        """
        allowed_actions = {}
        
        # Для атакующего игрока
        attacker_actions = [PlayerAction.ATTACK, PlayerAction.PASS, PlayerAction.QUIT]
        allowed_actions[self.game.current_attacker_id] = attacker_actions
        
        # Для защищающегося игрока
        defender_actions = [PlayerAction.DEFEND, PlayerAction.COLLECT, PlayerAction.QUIT]
        allowed_actions[self.game.current_defender_id] = defender_actions
        
        # Для остальных игроков только выход
        for player in self.game.players:
            if player.id_ != self.game.current_attacker_id and player.id_ != self.game.current_defender_id:
                allowed_actions[player.id_] = [PlayerAction.QUIT]
        
        return allowed_actions

    def get_state_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию о текущем состоянии
        
        Returns:
            Dict[str, Any]: Информация о состоянии
        """
        return {
            "attacker_id": self.game.current_attacker_id,
            "defender_id": self.game.current_defender_id,
            "table_cards": [str(card) for card in self.game.game_table.table_cards]
        }

    class PlayRoundWithThrowState(GameState, ExtraThrowActionMixin):
        """
        Состояние игры с использованием дополнительного броска карты
        """
        def __init__(self, game: FoolGame):
            super().__init__(game)
        
