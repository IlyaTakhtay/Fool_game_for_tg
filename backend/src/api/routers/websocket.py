import logging

from pydantic import TypeAdapter, ValidationError
from dishka import FromDishka
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from dishka.integrations.fastapi import inject
from redis.asyncio import Redis

from backend.src.api.exceptions import PlayerNotInGameError
from backend.src.api.managers.game_manager import GameManager
from backend.src.api.managers.connection_managaer import DistributedConnectionManager
from backend.src.api.models.websocket.enums import OutgoingMessageType
from backend.src.api.models.websocket.requests import IncomingMessage
from backend.src.api.routers.websocket_handlers import MessageRouter
from backend.src.settings import AppSettings
from backend.src.game.contracts.game_errors import GameLogicError

app_settings = AppSettings()
router = APIRouter(prefix=f"/api/{app_settings.api_version_prefix}", tags=["Games"])
logger = logging.getLogger(__name__)


@router.websocket("/ws/{game_id}")
@inject
async def websocket_game(
    websocket: WebSocket,
    game_id: str,
    player_id: str,
    gm: FromDishka[GameManager],
    cm: FromDishka[DistributedConnectionManager],
    redis: FromDishka[Redis],
):
    """Основная точка входа для WebSocket-соединения игры."""
    logger.info(
        f"WebSocket: Проверка авторизации игрока {player_id} для игры {game_id}"
    )
    try:
        game = await gm.get_player_game(player_id)
        if not game or game.game_id != game_id:
            reason = f"Игрок {player_id} не авторизован для игры {game_id}."
            logger.warning(reason)
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=reason)
            return
    except PlayerNotInGameError as e:
        logger.warning(f"Ошибка авторизации WebSocket: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(e))
        return

    try:
        await cm.connect(player_id, game_id, websocket)
        await gm.publish_full_game_state(game)
        validate_adapter = TypeAdapter(IncomingMessage)
        # Основной цикл обработки сообщений
        while True:
            json_data = await websocket.receive_json()

            try:
                message = validate_adapter.validate_python(json_data)
                logger.debug(f"Полученная сериализованная модель {message}")

                async with redis.lock(f"lock:game:{game_id}", timeout=10):
                    current_game_state = await gm.get_game_by_id(game_id)
                    logger.info(
                        f"Получено сообщение от {player_id} в игре {game_id}: тип={message.type}"
                    )
                    await MessageRouter.route(
                        message, player_id, current_game_state, gm
                    )

            except ValidationError as e:
                logger.warning(f"Ошибка валидации от {player_id}: {e}")
                await send_error_to_client(
                    websocket, "Invalid message format", "VALIDATION_ERROR", e.errors()
                )

            except GameLogicError as e:
                logger.warning(f"Игровая ошибка для {player_id}: {e}")
                await send_error_to_client(websocket, str(e), e.error_code)
                await gm.publish_player_game_state(player_id, current_game_state)

            except Exception as e:
                logger.error(
                    f"Неожиданная ошибка при обработке сообщения от {player_id}: {e}",
                    exc_info=True,
                )
                await send_error_to_client(
                    websocket, "Internal server error", "INTERNAL_ERROR"
                )

    except WebSocketDisconnect:
        logger.info(f"Игрок {player_id} отключился (WebSocketDisconnect).")

    except Exception as e:
        logger.error(
            f"Критическая ошибка WebSocket для {player_id} в игре {game_id}: {e}",
            exc_info=True,
        )

    finally:
        logger.info(f"Начало очистки ресурсов для игрока {player_id}.")
        try:
            await cm.disconnect(player_id)
        except Exception as e:
            logger.error(f"Ошибка при отключении {player_id} от ConnectionManager: {e}")
        try:
            await websocket.close()
        except Exception:
            pass
        logger.info(f"Соединение и ресурсы для игрока {player_id} полностью очищены.")


async def send_error_to_client(
    websocket: WebSocket,
    message: str,
    code: str = "ERROR",
    details: dict | list | None = None,
) -> None:
    """Отправляет ошибку клиенту по WebSocket"""
    error_response = {
        "type": OutgoingMessageType.ERROR,
        "data": {
            "message": message,
            "code": code,
        },
    }
    if details:
        error_response["data"]["details"] = details

    try:
        await websocket.send_json(error_response)
        
    except Exception as e:
        logger.warning(f"Не удалось отправить ошибку клиенту: {e}")
