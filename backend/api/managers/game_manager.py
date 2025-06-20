import time
from collections import deque
from uuid import uuid4

from backend.app.contracts.game_contract import PlayerAction, PlayerInput
from backend.app.models.game import FoolGame
from backend.app.utils.logger import setup_logger

logger = setup_logger(name="game-manager")

class GameManager:
    def __init__(self):
        self.player_to_game: dict[str, str] = {}  # player_id → game_id
        self.active_games: dict[str, FoolGame] = {}  # {game_id: FoolGame} - активные игры
        self.pending_games: dict[str, dict[str, FoolGame]] = {} # {free_slots: {game_id: FoolGame} - еще не заполненные игры
        self.last_activity = {}  # {game_id: timestamp}

    def add_game_to_player(self, game_id: str, player_id: str):
        """Вызывайте этот метод при добавлении игрока в игру."""
        logger.debug(f"add game to player: {game_id}, {player_id}")
        self.player_to_game[player_id] = game_id
        logger.debug(f"sss {self.player_to_game}")


    def remove_game_from_player(self, player_id: str) -> None:
        """Удаляет связь игрока с игрой"""
        if player_id in self.player_to_game:
            self.player_to_game.pop(player_id)

    @property
    def flatten_pending_games(self) -> list[FoolGame]:
        lst = []
        for games_dict in self.pending_games.values():
            for game in games_dict.values():
                lst.append(game)
        return lst

    def create_game(self, players_limit: int) -> FoolGame:
        game_id = str(uuid4())
        # logger.debug(f"game: {game_id}")
        game = FoolGame(game_id, players_limit)
        remaining_slots = int(players_limit - len(game.players))
        self.pending_games.setdefault(remaining_slots, {})[game_id] = game
        logger.debug(f"pending_games: {self.pending_games.keys()}")
        logger.debug(f"created_game: {game.game_id}")
        # self.last_activity[game_id] = time.time()
        return game

    def find_available_game(self) -> FoolGame | None:
        logger.debug(f"pend keys: {list(sorted(self.pending_games.keys()))}")
        for key in sorted(self.pending_games.keys(), reverse=True):
            if key == 0:
                continue
            game_rooms_dict = self.pending_games[key]
            logger.debug(f"{key}, rooms{game_rooms_dict.keys()})")
            try:
                game = game_rooms_dict[next(iter(game_rooms_dict))]
                logger.debug(f"{len(game.players)}")
                if game.is_full():
                    logger.debug("game is full")
                    return None 
                return game
            except StopIteration:
                continue
        return None
            
            
    def _find_game_by_id_in_pending(self, game_id: str) -> FoolGame | None:
        for games in self.pending_games.values():
            game = games.get(game_id)
            if game:
                return game
        return None

    def _find_game_by_id_in_active(self, game_id: str) -> FoolGame | None:
        logger.debug(f"get_game: {game_id}")
        logger.debug(f"active_games: {self.active_games}")
        return self.active_games.get(game_id, None)
    
    def get_game_by_id(self, game_id: str) -> FoolGame | None:
        if game := self._find_game_by_id_in_active(game_id):
            return game
        elif game := self._find_game_by_id_in_pending(game_id):
            return game
        return None

    def update_game_slots_by_id(self, game_id: str) -> None:
        """Обновляет категорию игры на основе свободных слотов."""
        # Сначала проверяем в active_games
        game = self.active_games.get(game_id)
        if not game:
            # Если нет в active_games, ищем в pending_games
            game = self._find_game_by_id_in_pending(game_id)
            if not game:
                logger.debug(f"Игра {game_id} не найдена")
                return

        remaining_slots = game.players_limit - len(game.players)
        logger.debug(f"Игра {game_id}: {len(game.players)}/{game.players_limit} игроков, {remaining_slots} свободных слотов")
        
        # Если есть свободные слоты и игра в состоянии лобби, она должна быть в pending_games
        if remaining_slots > 0 and game._current_state.__class__.__name__ == "LobbyState":
            # Если игра была в active_games, удаляем её оттуда
            if game_id in self.active_games:
                self.active_games.pop(game_id)
                logger.info(f"Игра {game_id} перемещена из active_games в pending_games")

            # Удаляем из текущей категории в pending_games, если там была
            for _, games in self.pending_games.items():
                if game_id in games:
                    games.pop(game_id)
                    break

            # Добавляем в правильную категорию в pending_games
            self.pending_games.setdefault(remaining_slots, {})[game_id] = game
            logger.debug(f"Игра {game_id} обновлена в pending_games с {remaining_slots} свободными слотами")

        # Если слотов нет или игра не в лобби, игра должна быть в active_games
        else:
            # Удаляем из pending_games, если там была
            for _, games in self.pending_games.items():
                if game_id in games:
                    games.pop(game_id)
                    break
            
            # Добавляем в active_games, если еще не там
            if game_id not in self.active_games:
                self.active_games[game_id] = game
                logger.info(f"Игра {game_id} перемещена в active_games (заполнена или не в лобби)")

    def get_game_by_player_id(self, player_id: str) -> FoolGame | None:
        logger.debug(f"Try to find player in game from {self.player_to_game}")
        game_id = self.player_to_game.get(player_id)
        if not game_id:
            return None
        return self.get_game_by_id(game_id)

    def handle_player_quit(self, game_id: str, player_id: str) -> None:
        """
        Обрабатывает выход игрока из игры.
        Атомарно обновляет все необходимые состояния.

        Args:
            game_id (str): ID игры
            player_id (str): ID игрока
        """
        game = self.get_game_by_id(game_id)
        if not game:
            return

        # Обрабатываем выход в игровой логике
        game.handle_input(
            player_input=PlayerInput(
                player_id=player_id,
                action=PlayerAction.QUIT,
            )
        )

        # Удаляем связь игрока с игрой
        self.remove_game_from_player(player_id)

        # Обновляем состояние игры в списках
        self.update_game_slots_by_id(game_id)
