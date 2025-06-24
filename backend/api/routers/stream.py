import asyncio
import json
import logging

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from backend.api.dependencies import get_game_manager
from backend.api.managers.game_manager import GameManager
from backend.app.models.game import FoolGame
from backend.app.config.settings import DEBUG

router = APIRouter(prefix="/api/v1", tags=["Games Stream"])
logger = logging.getLogger(__name__)

game_manager: GameManager = get_game_manager()


def get_games_list() -> list[dict]:
    """
    Собирает и форматирует список ожидающих игр.

    Returns:
        Список словарей, каждый из которых представляет ожидающую игру.
    """
    games = []
    for game in game_manager.flatten_pending_games:
        game: FoolGame
        games.append(
            {
                "game_id": game.game_id,
                "players_limit": game.players_limit,
                "players_inside": len(game.players),
            }
        )
    return games


@router.get("/games/stream")
async def stream_games(request: Request):
    """
    Создает Server-Sent Events (SSE) поток для отправки обновлений списка игр.

    Args:
        request: Объект запроса FastAPI.

    Returns:
        EventSourceResponse, который транслирует обновления клиенту.
    """

    async def event_generator():
        """Генерирует события для SSE потока."""
        last_hash = None
        ping_counter = 0
        player_id = request.query_params.get("player_id")

        try:
            while True:
                if await request.is_disconnected():
                    logger.info("SSE клиент отключился.")
                    break

                # Если игрок уже в игре, нет смысла слать ему список игр.
                if player_id and game_manager.get_game_by_player_id(player_id):
                    logger.info(
                        f"Игрок {player_id} уже в игре, остановка SSE потока."
                    )
                    yield {"event": "stop_stream", "data": "in_game"}
                    break

                games_list = get_games_list()
                current_hash = hash(json.dumps(games_list, sort_keys=True))

                if current_hash != last_hash:
                    logger.info("Список игр изменился, отправка обновления.")
                    yield {
                        "event": "message",
                        "data": json.dumps(games_list),
                    }
                    last_hash = current_hash
                    ping_counter = 0
                else:
                    ping_counter += 1
                    if ping_counter >= 10:  # (30 секунд / 3 секунды сна)
                        logger.debug("Отправка SSE ping для поддержания соединения.")
                        yield {"event": "ping", "data": "keep-alive"}
                        ping_counter = 0

                await asyncio.sleep(3)
        except asyncio.CancelledError:
            logger.info("SSE соединение закрыто сервером.")
        except Exception as e:
            logger.error(f"Ошибка в SSE потоке: {e}", exc_info=DEBUG)

    return EventSourceResponse(event_generator()) 