import logging
import msgspec.json

from pydantic import TypeAdapter, ValidationError
from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status
from redis.asyncio import Redis

from backend.src.api.exceptions import PlayerNotInGameError
from backend.src.api.managers.game_manager import GameManager
from backend.src.api.managers.connection_managaer import DistributedConnectionManager
from backend.src.api.models.websocket.enums import OutgoingMessageType
from backend.src.api.models.websocket.requests import IncomingMessage
from backend.src.api.v1.websocket_handlers import MessageRouter

from backend.src.game.contracts.game_errors import GameLogicError
from backend.src.api.dependencies.jwt_auth import verify_token

router = APIRouter(
    tags=["WebSocket"],
)
logger = logging.getLogger(__name__)


@router.websocket("/ws/{game_id}")
@inject
async def websocket_game(
    websocket: WebSocket,
    game_id: str,
    gm: FromDishka[GameManager],
    cm: FromDishka[DistributedConnectionManager],
    redis: FromDishka[Redis],
):
    """Основная точка входа для WebSocket-соединения игры."""

    access_token = None
    # Extract token from cookie headers
    for cookie in websocket.headers.get("cookie", "").split(";"):
        if "access_token" in cookie:
            access_token = cookie.split("=")[1]
            break

    if not access_token:
        reason = "Отсутствует токен доступа в куках."
        logger.warning(reason)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=reason)
        return

    try:
        current_user = verify_token(access_token)
        player_id = current_user["player_id"]
    except HTTPException as e:
        logger.warning(f"Ошибка аутентификации WebSocket: {e.detail}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=e.detail)
        return

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
            text_data = await websocket.receive_text()
            json_data = msgspec.json.decode(text_data)

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
        encoded_response = msgspec.json.encode(error_response)
        await websocket.send_text(encoded_response.decode("utf-8"))

    except Exception as e:
        logger.warning(f"Не удалось отправить ошибку клиенту: {e}")
