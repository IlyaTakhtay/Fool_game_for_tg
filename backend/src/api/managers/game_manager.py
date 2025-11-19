import logging
import asyncio
from uuid import uuid4
from typing import List

from redis.asyncio import Redis

from backend.src.api.exceptions import (
    GameNotFoundError,
    PlayerNotInGameError,
)
from backend.src.api.models.websocket.data import GameOverData
from backend.src.api.models.websocket.responses import (
    PlayerGameStateResponse,
    GameOverResponse,
)
from backend.src.game.contracts.game_contract import (
    ActionResult,
    PlayerInput,
    PlayerAction,
)
from backend.src.game.models.game import FoolGame
from backend.src.game.contracts.game_errors import GameLogicError
from backend.src.messaging.abstractions import AbstractEventBus
from backend.src.storage.repositories.interfaces import IGameRepository

logger = logging.getLogger(__name__)


class GameManager:
    """Сервисный слой для управления играми. Отвечает за бизнес-логику."""

    def __init__(
        self,
        game_repository: IGameRepository,
        event_bus: AbstractEventBus,
        redis_client: Redis,
    ):
        self._repo: IGameRepository = game_repository
        self._event_bus: AbstractEventBus = event_bus
        self._redis: Redis = redis_client

    async def create_game(self, players_limit: int) -> FoolGame:
        """Создать новую игру."""
        game = FoolGame(game_id=str(uuid4()), players_limit=players_limit)
        await self._repo.save(game)
        logger.info(f"Создана игра {game.game_id} со статусом: {game.status}")
        return game

    async def join_game(self, player_id: str, game_id: str | None = None) -> FoolGame:
        """Присоединить игрока к игре. Очереди здесь больше не создаются."""
        if not game_id:
            raise NotImplementedError("Поиск открытой игры еще не реализован")

        async with self._redis.lock(f"lock:game:{game_id}", timeout=10):
            game = await self._repo.get_by_id(game_id)
            if not game:
                raise GameNotFoundError(f"Игра {game_id} не найдена")

            player_input = PlayerInput(player_id=player_id, action=PlayerAction.JOIN)
            result = game.handle_input(player_input)

            if result.result != ActionResult.SUCCESS:
                raise GameLogicError(result.message, result.result)

            await self._repo.save(game)
            await self.publish_full_game_state(game)

        logger.info(f"Игрок {player_id} присоединился к игре {game.game_id}")
        return game

    async def exit_game(self, player_id: str):
        """Обрабатывает полный выход игрока из игры (не дисконнект)."""
        game = await self._repo.find_by_player_id(player_id)
        if not game:
            raise PlayerNotInGameError(f"Игрок {player_id} не состоит в игре")

        player_input = PlayerInput(player_id=player_id, action=PlayerAction.QUIT)
        game.handle_input(player_input)

        logger.info(f"Игрок {player_id} вышел из игры {game.game_id}")

        if not game.players:
            await self.delete_game(game.game_id)
            logger.info(f"Игра {game.game_id} удалена, т.к. в ней не осталось игроков.")
        else:
            await self._repo.save(game)
            await self.publish_full_game_state(game)

    async def get_player_game(self, player_id: str) -> FoolGame:
        """Получить игру игрока."""
        game = await self._repo.find_by_player_id(player_id)
        if not game:
            raise PlayerNotInGameError(f"Игрок {player_id} не найден ни в одной игре")
        return game

    async def get_game_by_id(self, game_id: str) -> FoolGame:
        """Получить игру по ID."""
        game = await self._repo.get_by_id(game_id)
        if not game:
            raise GameNotFoundError(f"Игра {game_id} не найдена")
        return game

    async def get_pending_games(
        self, limit: int = 100, offset: int = 0
    ) -> list[FoolGame]:
        """Получить список игр в лобби."""
        return await self._repo.find_by_status("pending", limit, offset)

    async def save_game(self, game: FoolGame):
        """Сохранить состояние игры."""
        await self._repo.save(game)
        logger.debug(f"Игра {game.game_id} сохранена в Redis")

    async def publish_full_game_state(self, game: FoolGame):
        """
        Готовит персональное состояние для каждого игрока и публикует
        его по персональному ключу маршрутизации.
        """
        all_players_in_game = game.players

        for player in all_players_in_game:
            player_specific_state = game.get_state_for_player(player.id_)
            if not player_specific_state:
                continue

            response_model = PlayerGameStateResponse(data=player_specific_state)
            routing_key = f"game.{game.game_id}.player.{player.id_}"

            await self._event_bus.publish(routing_key=routing_key, event=response_model)
        logger.debug(f"Опубликованы персональные состояния для игры {game.game_id}")

    async def publish_player_game_state(self, player_id: str, game: FoolGame):
        """
        Готовит персональное состояние для конкретного игрока и публикует
        его по персональному ключу маршрутизации.
        """
        player_specific_state = game.get_state_for_player(player_id)
        if not player_specific_state:
            logger.warning(
                f"Не удалось получить состояние для игрока {player_id} в игре {game.game_id}"
            )
            return

        response_model = PlayerGameStateResponse(data=player_specific_state)
        routing_key = f"game.{game.game_id}.player.{player_id}"

        await self._event_bus.publish(routing_key=routing_key, event=response_model)
        logger.debug(
            f"Опубликовано персональное состояние для игрока {player_id} в игре {game.game_id}"
        )

    async def publish_game_over_event(
        self, game: FoolGame, winner_id: str, loser_ids: List[str]
    ):
        """Публикует готовое событие окончания игры в шину событий."""

        response_model = GameOverResponse(
            data=GameOverData(
                winner_id=winner_id,
                loser_ids=loser_ids,
            )
        )

        await self._event_bus.publish(
            routing_key=f"game.{game.game_id}.game_over",
            event=response_model,
        )
        logger.info(f"Опубликовано событие окончания игры {game.game_id}")

    async def delete_game(self, game_id: str):
        """Удалить игру."""
        await self._repo.delete(game_id)
        logger.info(f"Игра {game_id} удалена")
