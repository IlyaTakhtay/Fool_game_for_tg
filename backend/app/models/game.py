import logging
import traceback
from typing import Any, Dict, List, Optional, Tuple, Union

from backend.app.utils.game_interface import Game, GameState
from backend.app.states.lobby_state import LobbyState
from backend.app.states.deal_state import DealState
from backend.app.states.game_over import GameOverState
from backend.app.states.play_round_state import PlayRoundWithoutThrowState
from backend.app.models.deck import Deck
from backend.app.models.player import Player, PlayerStatus
from backend.app.models.card_table import CardTable
from backend.app.contracts.game_contract import (
    PlayerInput,
    PlayerAction,
    ActionResult,
    StateResponse,
    StateTransition,
)

logger = logging.getLogger(__name__)


class FoolGame(Game):
    """Основной класс игры, который управляет состояниями и предоставляет API для взаимодействия"""

    def __init__(self, game_id: Optional[str], players_limit):
        if players_limit < 2:
            raise ValueError("Минимальное количество игроков должно быть 2 или больше")
        self.game_id: Optional[str] = game_id
        self.players_limit = players_limit
        self.players: List[Player] = list()
        self.deck: Deck = Deck()
        self.game_table: CardTable = CardTable()
        self.state_history: list[str] = list()
        self.current_attacker_id: str | None = None
        self.current_defender_id: str | None = None
        self._current_state: GameState = LobbyState(self)
        self.round_defender_status: PlayerAction | None = None

    @property
    def current_state_name(self) -> str:
        """Возвращает имя текущего состояния."""
        return self._current_state.__class__.__name__

    @property
    def current_attacker_idx(self) -> int | None:
        if self.current_attacker_id is not None:
            for i, player in enumerate(self.players):
                if player.id_ == self.current_attacker_id:
                    return i
        return None

    @property
    def current_defender_idx(self) -> int | None:
        if self.current_defender_id is not None:
            for i, player in enumerate(self.players):
                if player.id_ == self.current_defender_id:
                    return i
        return None

    def get_player_by_id(self, player_id: str) -> Player | None:
        """
        Возвращает игрока по его ID

        Args:
            player_id (str): ID игрока

        Returns:
            Player | None: Объект игрока или None, если игрок не найден
        """
        if player_id is not None:
            return next(
                (
                    player
                    for player in self.players
                    if player.id_ == player_id
                ),
                None,
            )
        return None

    def _set_state(self, new_state: GameState) -> StateTransition:
        """
        Изменяет текущее состояние игры

        Args:
            new_state: Новое состояние

        Returns:
            StateTransition: Информация о новом состоянии
        """
        exit_info = {}
        previous_state = None
        # Сохраняем предыдущее состояние
        try:
            if self._current_state:
                previous_state = self._current_state.__class__.__name__
                logger.debug(
                    f"Переключение состояния: {previous_state} -> {new_state.__class__.__name__}"
                )
                exit_info = self._current_state.exit()
                self.state_history.append(previous_state)
            # Переключаемся на новое состояние
            self._current_state = new_state
            enter_info = self._current_state.enter()
        except Exception as e:
            tb_str = traceback.format_exc()  # Получаем строку с полным трейсбеком
            logger.error(
                f"Ошибка в {__file__}, строка {traceback.extract_tb(e.__traceback__)[-1].lineno}:\n{tb_str}"
            )
            raise e
        # Если предыдущее состояние существует, сохраняем информацию о его выходе
        # Возвращаем информацию об изменении состояния
        return StateTransition(
            previous_state=previous_state,
            new_state=self._current_state.__class__.__name__,
            exit_info=exit_info,
            enter_info=enter_info,
        )

    def handle_input(self, player_input: PlayerInput) -> StateResponse | StateTransition | None:
        if not self._current_state:
            return StateResponse(ActionResult.INVALID_ACTION, "No active state")

        logger.debug(f"Обработка ввода игрока: {player_input} в состоянии {self.current_state_name}")
        response = self._current_state.handle_input(player_input)

        if not response:
            logger.debug("Обработка ввода не вернула ответа (response is None).")
            return None # Или можно вернуть осмысленный StateResponse

        logger.debug(f"Результат обработки ввода: {response}")

        if (
            hasattr(response, 'next_state') and response.next_state and
            response.next_state != self._current_state.__class__.__name__
        ):
            logger.info(f"Смена состояния: {self.current_state_name} -> {response.next_state}")
            
            state_class = next((s for s in GameState.__subclasses__() if s.__name__ == response.next_state), None)
            
            if state_class:
                return self._set_state(state_class(self))
            
            logger.warning(f"Состояние {response.next_state} не найдено.")
            return StateResponse(ActionResult.INVALID_ACTION, f"State {response.next_state} not found")

        return response

    def get_game_state(self) -> Dict[str, Any]:
        """
        Возвращает полную информацию о текущем состоянии игры

        Returns:
            Dict[str, Any]: Полная информация о состоянии игры
        """
        state_info = self._current_state.get_state_info() if self._current_state else {}

        return {
            "current_state": self._current_state.__class__.__name__ if self._current_state else None,
            "state_info": state_info,
            "players": [
                {"id": p.id_, "name": p.name, "cards_count": len(p.get_cards())}
                for p in self.players
            ],
            "trump_card": str(self.deck.trump_card) if self.deck.trump_card else None,
            "table_cards": [str(card) for card in self.game_table.table_cards],
            "deck_remaining": len(self.deck) if self.deck else None,
            "attacker_id": self.current_attacker_id,
            "defender_id": self.current_defender_id,
            "allowed_actions": (
                self._current_state.get_allowed_actions() if self._current_state else {}
            ),
        }

    def is_full(self):
        return len(self.players) == self.players_limit

    def get_player_position(self, player_id: str) -> int | None:
        """Получить позицию игрока за столом"""
        for i, player in enumerate(self.players):
            if player.id_ == player_id:
                return i + 1
        return None

    def reset_to_lobby(self):
        """Resets the game to a clean lobby state for a new game."""
        logger.info(f"Resetting game {self.game_id} to lobby state.")
        for player in self.players:
            player.clear_hand()
            player.status = PlayerStatus.UNREADY
        
        self.round_defender_status = None
        # The transition to LobbyState will call its `enter` method,
        # which already resets the deck, table, and attacker/defender IDs.
        self._set_state(LobbyState(self))

    def get_allowed_actions(self) -> Dict[str, List[str]]:
        """
        Delegates getting allowed actions to the current state.
        """
        if self._current_state and hasattr(self._current_state, "get_allowed_actions"):
            return self._current_state.get_allowed_actions()
        # Return a default (e.g., only QUIT) if no state or method exists
        return {p.id_: [PlayerAction.QUIT.name] for p in self.players}

    def _initialize_states(self):
        from backend.app.states.lobby_state import LobbyState
        from backend.app.states.play_round_state import (
            PlayRoundWithoutThrowState,
            PlayRoundWithThrowState,
            PlayRoundWithThrowAndDefendState,
            PlayRoundWithThrowAndDefendAndAttackState,
        )
