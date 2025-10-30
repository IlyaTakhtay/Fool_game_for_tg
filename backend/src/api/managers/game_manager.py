import logging
from uuid import uuid4
from typing import List, Set


from backend.src.api.exceptions import (
    GameNotFoundError,
    PlayerAlreadyInGameError,
    PlayerNotInGameError,
)
from backend.src.game.contracts.game_contract import (
    ActionResult,
    PlayerInput,
    PlayerAction,
)
from backend.src.game.models.game import FoolGame
from backend.src.game.states.lobby_state import LobbyState
from backend.src.game.utils.errors import GameLogicError
from backend.src.storage.repositories.interfaces import IGameRepository


logger = logging.getLogger(__name__)


class GameManager:
    """Сервисный слой для управления играми"""

    def __init__(self, game_repository: IGameRepository):
        self._repo = game_repository

    async def create_game(self, players_limit: int) -> FoolGame:
        """Создать новую игру"""

        game = FoolGame(
            game_id=str(uuid4()), players_limit=players_limit
        )  # TODO: who responsible for game id
        await self._repo.save(game)

        logger.info(f"Creating game {game.game_id} with status: {game.status}")

        return game

    async def join_game(self, player_id: str, game_id: str | None = None) -> FoolGame:
        """Присоединить игрока к игре"""
        if game_id:
            game = await self._repo.get_by_id(game_id)
            if not game:
                raise GameNotFoundError(f"Game {game_id} not found")

        player_input = PlayerInput(player_id=player_id, action=PlayerAction.JOIN)
        result = game.handle_input(player_input)

        if result.result != ActionResult.SUCCESS:
            raise GameLogicError(result.message)

        await self._repo.save(game)

        logger.info(f"Игрок {player_id} присоединился к игре {game.game_id}")
        return game

    async def exit_game(self, player_id: str) -> FoolGame:
        """Выйти из игры"""
        game = await self._repo.find_by_player_id(player_id)
        if not game:
            raise PlayerNotInGameError(f"Player {player_id} not in any game")
        player_input = PlayerInput(player_id=player_id, action=PlayerAction.QUIT)
        result = game.handle_input(player_input)

        if result.result != ActionResult.SUCCESS:
            raise GameLogicError(result.message)

        await self._repo.save(game)
        logger.info(f"Игрок {player_id} вышел из игры {game.game_id}")
        return game

    async def get_player_game(self, player_id: str) -> FoolGame:
        """Получить игру игрока"""
        game = await self._repo.find_by_player_id(player_id)
        if not game:
            raise PlayerNotInGameError(f"Player {player_id} not in any game")
        return game

    async def get_game_by_id(self, game_id: str) -> FoolGame:
        """Получить игру по ID"""
        game = await self._repo.get_by_id(game_id)
        if not game:
            raise GameNotFoundError(f"Game {game_id} not found")
        return game

    async def get_pending_games(
        self, limit: int = 100, offset: int = 0
    ) -> list[FoolGame]:
        """Получить список игр в лобби"""
        return await self._repo.find_by_status("pending", limit, offset)

    async def save_game(self, game: FoolGame):
        """Сохранить состояние игры"""
        await self._repo.save(game)
        logger.debug(f"Игра {game.game_id} сохранена в Redis")

    async def delete_game(self, game_id: str):
        """Удалить игру"""
        await self._repo.delete(game_id)
        logger.info(f"Игра {game_id} удалена")
