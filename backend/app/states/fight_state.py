from __future__ import annotations
from typing import Dict, List, Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.app.models.game import FoolGame

from backend.app.utils.game_interface import GameState
from backend.app.models.player import Player, PlayerStatus
from backend.app.contracts.game_contract import PlayerInput, PlayerAction, ActionResult, StateResponse, StateTransition

class FightState(GameState):
    """Состояние атаки в игре Дурак, для игры без подбрасывания"""
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
            return StateResponse(
                ActionResult.SUCCESS,
                f"Игрок {player_input.player_id} покинул игру. Игра завершена.",
                "LobbyState",
                {"players_count": len(self.game.players)}
            )
        
        # Проверяем, что ход принадлежит атакующему или защищающемуся игроку
        if player_input.player_id != self.game.current_attacker_id and player_input.player_id != self.game.current_defender_id:
            return StateResponse(
                ActionResult.NOT_YOUR_TURN,
                "Сейчас не ваш ход.",
                None,
                None
            )
        
        # Обработка атаки
        if player_input.action == PlayerAction.ATTACK and player_input.player_id == self.game.current_attacker_id:
            # Проверяем, что карта для атаки указана
            if not player_input.attack_card:
                return StateResponse(
                    ActionResult.CARD_REQUIRED,
                    "Необходимо выбрать карту для атаки.",
                    None,
                    None
                )
            
            # Проверяем, что карта есть у игрока
            attacker = next((p for p in self.game.players if p.id == player_input.player_id), None)
            if not attacker or player_input.attack_card not in attacker.cards:
                return StateResponse(
                    ActionResult.INVALID_CARD,
                    "У вас нет такой карты.",
                    None,
                    None
                )
            
            result = self.game.game_table.throw_card(player_input.attack_card)
            
            # Проверяем правила подкидывания (если стол не пуст)
            if self.game.game_table.table_cards and result["status"] == "failed":
                if result["message"] == "no free slots":
                    return StateResponse(
                        ActionResult.TABLE_FULL,
                        "Стол полный",
                        None,
                        None
                    )
                if result["message"] == "wrong rank":
                    return StateResponse(
                        ActionResult.WRONG_CARD,
                        "Эту карту нельзя подкинуть. Можно подкидывать только карты тех же достоинств, что уже есть на столе.",
                        None,
                        None
                    )
            
            # Проверка на то, что у игрока достаточно карт для защиты
            defender = next((p for p in self.game.players if p.id == self.game.current_defender_id), None)
            if defender and len(defender.cards) <= len(self.game.game_table.table_cards):
                return StateResponse(
                    ActionResult.TABLE_FULL,
                    "У защищающегося недостаточно карт для защиты ещё одной",
                    None,
                    None
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
        
        # Обработка защиты
        if player_input.action == PlayerAction.DEFEND and player_input.player_id == self.game.current_defender_id:
            # Проверка наличия карты для защиты
            if not player_input.defend_card:
                return StateResponse(
                    ActionResult.CARD_REQUIRED,
                    "Необходимо выбрать карту для защиты.",
                    None,
                    None
                )
            
            # Проверяем, что карта есть у игрока
            defender = next((p for p in self.game.players if p.id == player_input.player_id), None)
            if not defender or player_input.defend_card not in defender.cards:
                return StateResponse(
                    ActionResult.INVALID_CARD,
                    "У вас нет такой карты.",
                    None,
                    None
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
                    None,
                    None
                )

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
        
        # Обработка паса (пропуска хода) атакующим
        if player_input.action == PlayerAction.PASS and player_input.player_id == self.game.current_attacker_id:
            # Проверяем, отбил ли защищающийся все карты
            if self._all_cards_defended():
                # Все карты отбиты, переходим к следующему раунду
                result = self.update_after_successful_defense()
                return StateResponse(
                    ActionResult.SUCCESS,
                    f"Игрок {self.game.current_defender_id} успешно отбился. Новый атакующий: {self.game.current_attacker_id}",
                    None,
                    {
                        "attacker_id": self.game.current_attacker_id,
                        "defender_id": self.game.current_defender_id,
                        "table_cards": []
                    }
                )
            else:
                return StateResponse(
                    ActionResult.INVALID_ACTION,
                    "Нельзя пасовать, пока защищающийся не отбил все карты.",
                    None,
                    None
                )
        
        # Обработка сбора карт защищающимся
        if player_input.action == PlayerAction.COLLECT and player_input.player_id == self.game.current_defender_id:
            # Переходим в состояние добора
            return StateResponse(
                ActionResult.SUCCESS,
                f"Игрок {player_input.player_id} не смог отбить карты",
                "OnlyThrowState",
                None
            )
        
        # Если действие не распознано
        return StateResponse(
            ActionResult.INVALID_ACTION,
            "Недопустимое действие в состоянии атаки.",
            None,
            None
        )
    
    def update_after_successful_defense(self) -> Dict[str, Any]:
        """
        Обновляет состояние игры после успешной защиты
        
        Returns:
            Dict[str, Any]: Информация о новом состоянии
        """
        # Очищаем стол
        self.game.game_table.clear_table()
        
        # Защищающийся становится атакующим
        new_attacker_id = self.game.current_defender_id
        
        # Находим индекс нового атакующего
        try:
            attacker_index = [p.id for p in self.game.players].index(new_attacker_id)
        except ValueError:
            attacker_index = 0
        
        # Определяем индекс следующего защищающегося (по часовой стрелке)
        next_defender_index = (attacker_index + 1) % len(self.game.players)
        
        # Обновляем ID атакующего и защищающегося
        self.game.current_attacker_id = new_attacker_id
        self.game.current_defender_id = self.game.players[next_defender_index].id
        
        # Добираем карты из колоды
        self._deal_cards()
        
        return {
            "message": f"Новый атакующий: {self.game.current_attacker_id}",
            "attacker_id": self.game.current_attacker_id,
            "defender_id": self.game.current_defender_id
        }
    
    def _deal_cards(self) -> None:
        """
        Раздает карты игрокам из колоды до 6 штук
        """
        attacker_idx = [p.id for p in self.game.players].index(self.game.current_attacker_id)
        sorted_players = self.game.players[attacker_idx:] + self.game.players[:attacker_idx]
        
        # Раздаем карты
        for player in sorted_players:
            if player.id == self.game.current_defender_id:
                continue
            while len(player.cards) < 6:
                if (draw_card := self.game.deck.draw()) is not None:
                    player.add_card(draw_card)
                else:
                    break
                
        # Проверяем, есть ли победитель
        for player in self.game.players:
            if len(player.cards) == 0 and len(self.game.deck) == 0:
                # У игрока нет карт и колода пуста - он победил
                player.status = PlayerStatus.VICTORY
                # self._handle_game_end(player.id)
                # return

        defender = next((p for p in self.game.players if p.id == self.game.current_defender_id), None)
        if defender:
            while len(defender.cards) < 6:
                if (draw_card := self.game.deck.draw()) is not None:
                    defender.add_card(draw_card)
                else:
                    break
        
        # Проверяем, остались ли игроки с картами
        players_with_cards = [p for p in self.game.players if len(p.cards) > 0]
        if len(players_with_cards) == 1 and len(self.game.deck) == 0:
            # Остался только один игрок с картами - он проиграл
            self._handle_game_end(None, loser_id=players_with_cards[0].id)

    def _handle_game_end(self, winner_id=None, loser_id=None): # Тут чето перепридумать надо
        """Обрабатывает окончание игры"""
        # if winner_id:
        #     # Отправляем событие о победе
        #     self.game.event_manager.send_event("game_end", {
        #         "winner_id": winner_id,
        #         "message": f"Игрок {winner_id} победил!"
        #     })
        # elif loser_id:
        #     # Отправляем событие о проигрыше
        #     self.game.event_manager.send_event("game_end", {
        #         "loser_id": loser_id,
        #         "message": f"Игрок {loser_id} проиграл!"
        #     })
        
        # Переходим в состояние окончания игры
        self.game.set_state("GameOverState")


    def _all_cards_defended(self) -> bool:
        """
        Проверяет, все ли карты на столе отбиты
        
        Returns:
            bool: True, если все карты отбиты, иначе False
        """
        if not all(card.get("defend_card") for card in self.game.game_table.table_cards):
            return False
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
            if player.id != self.game.current_attacker_id and player.id != self.game.current_defender_id:
                allowed_actions[player.id] = [PlayerAction.QUIT]
        
        return allowed_actions
    def update(self):
        return print(
            'TODO'
        )
    
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
