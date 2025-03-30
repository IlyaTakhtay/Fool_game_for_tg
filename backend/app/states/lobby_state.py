from __future__ import annotations
from typing import Dict, List, Any, Optional
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.app.models.game import FoolGame

from backend.app.utils.game_interface import GameState

from backend.app.models.player import Player, PlayerStatus
from backend.app.contracts.game_contract import PlayerInput, PlayerAction, ActionResult, StateResponse
class LobbyState(GameState):
    """Состояние ожидания игроков перед началом игры"""
    def __init__(self, game: FoolGame) -> None:
        self.game: FoolGame = game
 
    def enter(self) -> Dict[str, Any]:
        """
        Инициализирует состояние лобби
        
        Returns:
            Dict[str, Any]: Информация о входе в состояние лобби
        """
        # Сбрасываем игровые переменные на случай, если это новая игра
        self.game.deck.generate_deck()
        self.game.game_table.clear_table()
        self.game.current_attacker_id = None
        self.game.current_defender_id = None
        
        return {
            "message": f"Ожидание игроков. Минимум ${self.game.players_limit} игрок(ов) необходимо для начала игры.",
            "players_count": len(self.game.players),
        }
    
    def exit(self) -> Dict[str, Any]:
        """
        Вызывается при выходе из состояния лобби
        
        Returns:
            Dict[str, Any]: Информация о результатах состояния
        """
        # Подготовка к началу игры
        # self.game.deck.shuffle()
        
        # Раздача карт игрокам
        for player in self.game.players:
            player.cards = self.game.deck.draw_cards(6)
        
        # Определение первого атакующего (у кого наименьший козырь)
        self.game.current_attacker_id = self._determine_first_attacker()
        
        self.game.current_defender_id = self._determine_defender()
        return {
            "message": "Игра начинается!",
            "players_count": len(self.game.players),
            "first_attacker": self.game.current_attacker_id,
            "first_defender": self.game.current_defender_id,
            "trump_suit": str(self.game.deck.trump_card.suit)
        }
    
    def handle_input(self, player_input: PlayerInput) -> StateResponse:
        """
        Обрабатывает ввод игрока в лобби
        
        Args:
            player_input: Входные данные об игроке
            
        Returns:
            StateResponse: Результат обработки ввода
        """
        # Обработка выхода игрока
        if player_input.action == PlayerAction.QUIT:
            # Удаляем игрока из списка
            self.game.players = [p for p in self.game.players if p.id != player_input.player_id]
            return StateResponse(
                ActionResult.SUCCESS,
                f"Игрок {player_input.player_id} покинул игру",
                None,
                {"players_count": len(self.game.players)}
            )

        # Обработка установки статуса "готов"
        if player_input.action == PlayerAction.READY:
            # Находим игрока и меняем его статус
            player = next((p for p in self.game.players if p.id == player_input.player_id), None)
            if player:
                player.status = PlayerStatus.READY
                
                # Проверяем, все ли игроки готовы и достигнут ли лимит
                if (len(self.game.players) == self.game.players_limit and 
                    all(pl.status == PlayerStatus.READY for pl in self.game.players)):
                    return StateResponse(
                        ActionResult.SUCCESS,
                        "Все игроки готовы. Начинаем игру!",
                        "AttackState",  # Переход к состоянию атаки
                        {"players_count": len(self.game.players)}
                    )
                
                return StateResponse(
                    ActionResult.SUCCESS,
                    f"Игрок {player_input.player_id} готов к игре.",
                    None,
                    {"players_count": len(self.game.players)}
                )
            else:
                return StateResponse(
                    ActionResult.INVALID_ACTION,
                    "Игрок не найден",
                    None,
                    None
                )

        # Обработка присоединения к игре
        if player_input.action == PlayerAction.JOIN:
            # Проверяем, есть ли уже этот игрок в списке
            if any(p.id == player_input.player_id for p in self.game.players):
                return StateResponse(
                    ActionResult.INVALID_ACTION,
                    "Вы уже присоединились к игре",
                    None,
                    None
                )
            
            # Проверяем, не достигнуто ли максимальное количество игроков
            if len(self.game.players) >= self.game.players_limit:
                return StateResponse(
                    ActionResult.ROOM_FULL,
                    "Достигнуто максимальное количество игроков",
                    None,
                    None
                )
            
            # Добавляем нового игрока
            new_player = Player(player_input.player_id, f"Player {player_input.player_id}") #TODO: вытаскивать потом из бд
            self.game.players.append(new_player)
            
            # Проверяем, можно ли начать игру (все игроки присоединились и готовы)
            if len(self.game.players) == self.game.players_limit:
                switch_state=self.update(player_input)
                if not switch_state:
                    return StateResponse(
                        ActionResult.SUCCESS,
                        f"Игрок {player_input.player_id} готов. Ожидание готовности всех игроков.",
                        None,
                        {"players_count": len(self.game.players)}
                    )
                else:
                    return switch_state
            
            return StateResponse(
                ActionResult.SUCCESS,
                f"Игрок {player_input.player_id} присоединился. Ожидание других игроков.",
                None,
                {"players_count": len(self.game.players)}
            )

        # Если действие не распознано
        return StateResponse(
            ActionResult.INVALID_ACTION,
            "Недопустимое действие в лобби",
            None,
            None
        )
    

    def update(self, player_input: Player) -> Optional[StateResponse]:
        """
        Проверяет условия для перехода в другое состояние
        
        Returns:
            Optional[str]: Имя следующего состояния или None
        """
        # Автоматический переход в состояние атаки если все игроки готовы и 
        if all(pl.status == PlayerStatus.READY for pl in self.game.players) and len(self.game.players) == self.game.players_limit:
            return StateResponse(
                            ActionResult.SUCCESS,
                            f"Игрок {player_input.player_id} присоединился. Все игроки готовы. Начинаем игру!",
                            "AttackState",
                            {"players_count": len(self.game.players)}
                    )
        return None
    
    def get_allowed_actions(self) -> Dict[int, List[PlayerAction]]:
        """
        Возвращает список разрешенных действий для каждого игрока
        
        Returns:
            Dict[int, List[PlayerAction]]: Словарь {id_игрока: [разрешенные_действия]}
        """
        allowed_actions = {}
        
        # Для уже присоединившихся игроков
        for player in self.game.players:
            actions = [PlayerAction.QUIT]
            
            # Если игрок еще не готов, добавляем действие READY
            if player.status != PlayerStatus.READY:
                actions.append(PlayerAction.READY)
                
            allowed_actions[player.id] = actions
        return allowed_actions

    def _determine_defender(self) -> str:
        """
        Определяет защищающегося игрока (следующий по кругу после атакующего)
        
        Returns:
            str: ID защищающегося игрока
        """
        try:
            attacker_index = [p.id for p in self.game.players].index(self.game.current_attacker_id)
        except ValueError:
            attacker_index = 0
        
        if len(self.game.players) < 2:
            raise ValueError("Нет игроков для определения защищающегося")
            
        defender_index = (attacker_index + 1) % len(self.game.players)
        return self.game.players[defender_index].id
    
    def _determine_first_attacker(self) -> int:
        """
        Определяет первого атакующего игрока (у кого наименьший козырь)
        
        Returns:
            int: ID первого атакующего игрока
        """
        trump_suit = self.game.deck.trump_card.suit
        min_trump_rank = None
        first_attacker_id = None
        
        # Ищем игрока с наименьшим козырем
        for player in self.game.players:
            trump_cards = [card for card in player.cards if card.suit == trump_suit]
            if trump_cards:
                min_player_trump = min(trump_cards, key=lambda card: card.rank.value)
                if min_trump_rank is None or min_player_trump.rank.value < min_trump_rank:
                    min_trump_rank = min_player_trump.rank.value
                    first_attacker_id = player.id
        
        # Если ни у кого нет козырей, выбираем первого игрока
        if first_attacker_id is None and self.game.players:
            first_attacker_id = self.game.players[0].id
            
        return first_attacker_id
