import asyncio
import json
import logging

from dishka import FromDishka
from fastapi import APIRouter, Request, Depends
from sse_starlette.sse import EventSourceResponse
from dishka.integrations.fastapi import DishkaRoute


from backend.src.api.exceptions import PlayerNotInGameError
from backend.src.api.managers.game_manager import GameManager
from backend.src.config import AppSettings
from backend.src.game.models.game import FoolGame
from backend.src.game.config.settings import DEBUG

app_settings = AppSettings()
router = APIRouter(
    prefix=f"/api/{app_settings.api_version_prefix}",
    tags=["Games Stream"],
    route_class=DishkaRoute,
)
logger = logging.getLogger(__name__)


async def get_games_list(
    gm: FromDishka[GameManager],
) -> list[dict]:
    """
    Собирает и форматирует список ожидающих игр.

    Returns:
        Список словарей, каждый из которых представляет ожидающую игру.
    """
    games = []
    for game in await gm.get_pending_games():
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
async def stream_games(
    gm: FromDishka[GameManager],
    request: Request,
):
    """
    Создает Server-Sent Events (SSE) поток для отправки обновлений списка игр.
    Args:
        request: Объект запроса FastAPI.
        gm: Экземпляр менеджера игр.

    Returns:
        EventSourceResponse, который транслирует обновления клиенту.
    """

    async def event_generator(gm: GameManager):
        """Генерирует события для SSE потока."""
        last_hash = None

        try:
            while True:
                if await request.is_disconnected():
                    logger.info("SSE клиент отключился.")
                    break

                games_list = await get_games_list(gm)
                current_hash = hash(json.dumps(games_list, sort_keys=True))

                if current_hash != last_hash:
                    logger.info("Список игр изменился, отправка обновления.")
                    yield {
                        "event": "message",
                        "data": json.dumps(games_list),
                    }
                    last_hash = current_hash
                else:
                    logger.debug("Отправка SSE ping для поддержания соединения.")
                    yield {"event": "ping", "data": "keep-alive"}
                await asyncio.sleep(3)
        except asyncio.CancelledError:
            logger.info("SSE соединение закрыто сервером.")
        except Exception as e:
            logger.error(f"Ошибка в SSE потоке: {e}", exc_info=DEBUG)

    return EventSourceResponse(event_generator(gm))
