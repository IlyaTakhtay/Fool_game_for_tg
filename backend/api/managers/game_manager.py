import logging
from uuid import uuid4
from typing import Dict, List

from backend.app.contracts.game_contract import PlayerInput, PlayerAction
from backend.app.models.game import FoolGame
from backend.app.states.lobby_state import LobbyState


logger = logging.getLogger(__name__)


class GameManager:
    """
    Управляет жизненным циклом игр: создание, поиск, перемещение
    между лобби и активной фазой.
    """

    def __init__(self):
        self.active_games: Dict[str, FoolGame] = {}  # Игры, которые идут
        self.pending_games: Dict[str, FoolGame] = {}  # Игры, ожидающие игроков
        self.player_to_game: Dict[str, str] = {}  # Связь player_id -> game_id

    def create_game(self, players_limit: int) -> FoolGame:
        """Создает новую игру и помещает ее в ожидание."""
        game_id = str(uuid4())
        game = FoolGame(game_id=game_id, players_limit=players_limit)
        self.pending_games[game.game_id] = game
        logger.info(f"Создана новая игра с ID: {game.game_id}")
        return game

    def get_game_by_id(self, game_id: str) -> FoolGame | None:
        """Получает игру по её ID из любого списка."""
        logger.debug(f"Поиск игры по ID: {game_id}")
        return self.active_games.get(game_id) or self.pending_games.get(game_id)

    def get_game_by_player_id(self, player_id: str) -> FoolGame | None:
        """Находит игру, в которой числится игрок."""
        logger.debug(f"Поиск игры для игрока: {player_id}")
        game_id = self.player_to_game.get(player_id)
        if not game_id:
            return None
        return self.get_game_by_id(game_id)

    def find_available_game(self) -> FoolGame | None:
        """Находит первую доступную игру в лобби со свободным местом."""
        for game in self.pending_games.values():
            if not game.is_full():
                return game
        logger.debug("Свободных игр в лобби не найдено.")
        return None

    def add_game_to_player(self, game_id: str, player_id: str) -> None:
        """Привязывает ID игры к ID игрока."""
        self.player_to_game[player_id] = game_id
        logger.debug(f"Игрок {player_id} привязан к игре {game_id}")

    def remove_game_from_player(self, player_id: str) -> None:
        """Удаляет привязку игрока к игре."""
        if player_id in self.player_to_game:
            del self.player_to_game[player_id]
            logger.debug(f"Удалена связь для игрока {player_id}")

    def update_game_slots_by_id(self, game_id: str) -> None:
        """Перемещает игру между pending и active в зависимости от ее состояния."""
        game = self.get_game_by_id(game_id)
        if not game:
            logger.warning(f"Попытка обновить несуществующую игру: {game_id}")
            return

        is_in_lobby = isinstance(game._current_state, LobbyState)
        is_full = game.is_full()

        # Перемещаем в active, если игра заполнилась или вышла из лобби
        if (is_full or not is_in_lobby) and game_id in self.pending_games:
            self.active_games[game_id] = self.pending_games.pop(game_id)
            logger.info(f"Игра {game_id} перемещена в active_games.")
        # Возвращаем в pending, если освободились места и игра еще в лобби
        elif not is_full and is_in_lobby and game_id in self.active_games:
            self.pending_games[game_id] = self.active_games.pop(game_id)
            logger.info(f"Игра {game_id} перемещена в pending_games.")

    def handle_player_quit(self, game_id: str, player_id: str):
        """Обрабатывает выход игрока, делегируя логику ядру игры."""
        game = self.get_game_by_id(game_id)
        if not game:
            logger.warning(f"Игра {game_id} не найдена для выхода игрока {player_id}")
            return

        # Ядро игры само изменит свое состояние
        game.handle_input(PlayerInput(player_id=player_id, action=PlayerAction.QUIT))

        self.remove_game_from_player(player_id)
        self.update_game_slots_by_id(game_id)
        logger.info(f"Выход игрока {player_id} из игры {game_id} обработан.")

    @property
    def flatten_pending_games(self) -> List[FoolGame]:
        """Возвращает плоский список игр, ожидающих игроков."""
        return list(self.pending_games.values())
