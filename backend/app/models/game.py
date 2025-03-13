from typing import Optional, Dict, Any, List

from backend.app.models.deck import Deck
from backend.app.models.player import Player
from backend.app.models.card_table import CardTable
from backend.app.states.game_state import GameState, LobbyState, PlayerInput, ActionResult, StateResponse, StateTransition

class FoolGame:
    """Основной класс игры, который управляет состояниями и предоставляет API для взаимодействия"""
    
    def __init__(self, game_id: Optional[str], players_limit):
        self.game_id: Optional[str] = game_id
        self.players_limit = players_limit
        self.players: List[Player] = list()
        self.deck: Deck = Deck()
        self.game_table: CardTable = CardTable()
        self.state_history = list()
        self.current_attacker_id = None
        self.current_defender_id = None
        self._current_state: GameState = LobbyState(self)
        
    def _set_state(self, new_state: GameState) -> StateTransition:
        """
        Изменяет текущее состояние игры
        
        Args:
            new_state: Новое состояние
            
        Returns:
            Dict[str, Any]: Информация о новом состоянии
        """
        exit_info = {}
        previous_state = None
        # Сохраняем предыдущее состояние
        if self._current_state:
            previous_state = self._current_state.name
            exit_info = self._current_state.exit()
            self.state_history.append(previous_state)
        # Переключаемся на новое состояние
        self._current_state = new_state
        enter_info = self._current_state.enter()
        
        # Возвращаем информацию об изменении состояния
        return StateTransition(
            previous_state=previous_state,
            new_state=self._current_state.name,
            exit_info=exit_info,
            enter_info=enter_info
        )
    
    # def get_cond_to_update_state(self) -> StateResponse: #TODO: мб не нужна
    #     """
    #     Возвращает недостающие условия для обновления состояния
        
    #     Returns:
            
    #     """
    

    def handle_input(self, player_input: PlayerInput) -> StateResponse|StateTransition:
        """
        Передает ввод текущему состоянию и обрабатывает результат
        
        Args:
            player_input: Структурированный ввод от игрока
            
        Returns: 
            StateResponse: Результат обработки ввода
        """
        if not self._current_state:
            return StateResponse(
                ActionResult.INVALID_ACTION,
                "No active state",
                None,
                None
            )
        
        response = self._current_state.handle_input(player_input)
        # Если нужно сменить состояние
        if response.next_state and response.next_state != self._current_state.__name__:
        # Находим класс состояния по имени и создаем экземпляр
            for state_class in GameState.__subclasses__():
                if state_class.__name__ == response.next_state:
                    transition = self._set_state(state_class(self))
                    return transition
            return StateResponse(
                ActionResult.INVALID_ACTION,
                f"State {response.next_state} not found",
                None,
                None
            )
        return response
    
    def get_game_state(self) -> Dict[str, Any]:
        """
        Возвращает полную информацию о текущем состоянии игры
        
        Returns:
            Dict[str, Any]: Полная информация о состоянии игры
        """
        state_info = self._current_state.get_state_info() if self._current_state else {}
        
        return {
            "current_state": self._current_state.name if self._current_state else None,
            "state_info": state_info,
            "players": [{"id": p.id, "name": p.name, "cards_count": len(p.cards)} for p in self.players],
            "trump_card": str(self.deck.trump_card) if self.deck.trump_card else None,
            "table_cards": [str(card) for card in self.game_table.table_cards],
            "deck_remaining": len(self.deck) if self.deck else None,
            "attacker_id": self.current_attacker_id,
            "defender_id": self.current_defender_id,
            "allowed_actions": self._current_state.get_allowed_actions() if self._current_state else {}
        }
