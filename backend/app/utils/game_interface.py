from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from backend.app.contracts.game_contract import PlayerInput, PlayerAction, ActionResult, StateResponse, StateTransition

class Game(ABC):
    @abstractmethod
    def __init__(self, game_id: Optional[str], players_limit: int):
        pass
    
    @abstractmethod
    def handle_input(self, player_input: PlayerInput) -> StateResponse|StateTransition:
        pass
    
    @abstractmethod
    def get_game_state(self) -> Dict[str, Any]:
        pass

# Определение интерфейса для игры
class GameState(ABC):
    def __init__(self, game: Game) -> None:
        self.game: Game = game
    """Абстрактный базовый класс для всех состояний игры с улучшенным интерфейсом"""
    
    @abstractmethod
    def enter(self) -> Dict[str, Any]:
        """
        Вызывается при входе в состояние
        
        Returns:
            Dict[str, Any]: Информация о состоянии для отображения
        """
        pass
    
    
    @abstractmethod
    def handle_input(self, player_input: PlayerInput) -> StateResponse:
        """
        Обрабатывает ввод игрока
        
        Args:
            player_input: Структурированный ввод от игрока
            
        Returns:
            StateResponse: Результат обработки ввода с информацией о следующем состоянии
        """
        pass
    
    @abstractmethod
    def exit(self) -> Dict[str, Any]:
        """
        Вызывается при выходе из состояния
        
        Returns:
            Dict[str, Any]: Информация о результатах состояния
        """
        pass

    @abstractmethod
    def update(self) -> Optional[StateResponse]:
        """
        Проверяет условия для перехода в другое состояние и обнолвяет состояние
        
        Returns:
           StateResponse: Результат обработки ввода с информацией о следующем состоянии
        """


    def get_state_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию о текущем состоянии
        
        Returns:
            Dict[str, Any]: Информация о состоянии
        """
        return {
            "state_name": self.__class__.__name__,
            "description": self.__doc__,
            "allowed_actions": self.get_allowed_actions()
        }
    
    @abstractmethod
    def get_allowed_actions(self) -> Dict[int, List[PlayerAction]]:
        """
        Возвращает список разрешенных действий для каждого игрока
        
        Returns:
            Dict[int, List[PlayerAction]]: Словарь {id_игрока: [разрешенные_действия]}
        """
        pass


