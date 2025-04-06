import time
from collections import deque
from uuid import uuid4

from backend.app.models.game import FoolGame
from backend.app.utils.logger import setup_logger

logger = setup_logger(name="game-manager")

class GameManager:
    def __init__(self):
        self.active_games: dict[str, FoolGame] = {}  # {game_id: FoolGame} - активные игры
        self.pending_games: dict[str, dict[str, FoolGame]] = {} # {free_slots: {game_id: FoolGame} - еще не заполненные игры
        self.last_activity = {}  # {game_id: timestamp}

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
        """Обновляет категорию игры в pending_games на основе свободных слотов."""
        game = self._find_game_by_id_in_pending(game_id)
        remaining_slots = game.players_limit - len(game.players)
        for _, games in self.pending_games.items():
            if game_id in games:
                games.pop(game_id)  # Удаляем игру из текущей категории
                break

        self.pending_games.setdefault(remaining_slots, {})[game_id] = game


    
    # def add_player_to_game(self, game_id: str, player_id: str) -> FoolGame:
    #     """Добавляет игрока в игру и возвращает обновленную игру."""
        

        

    #     while self.pending_games:
    #         game_id = self.pending_games.popleft()
    #         game = self.active_games.get(game_id)
    #         # Если игра существует и не заполнена, оставляем её в очереди
    #         if game and not game.is_full():
    #             temp_queue.append(game_id)
    #     self.pending_games = temp_queue


    
    # def cleanup_inactive(self, max_inactive_sec=86400):
    #     now = time.time()
    #     inactive = [
    #         game_id 
    #         for game_id, ts in self.last_activity.items()
    #         if now - ts > max_inactive_sec
    #     ]
        
    #     for game_id in inactive:
    #         del self.active_games[game_id]
    #         del self.last_activity[game_id]
