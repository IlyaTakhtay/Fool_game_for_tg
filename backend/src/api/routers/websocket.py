import logging

from dishka import FromDishka
from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect, status
from dishka.integrations.fastapi import inject

from backend.src.api.exceptions import PlayerNotInGameError
from backend.src.api.managers.game_manager import GameManager
from backend.src.api.managers.connection_managaer import ConnectionManager
from backend.src.api.models.websocket_models import MessageType
from backend.src.api.routers.websocket_handlers import (
    _send_full_game_state_to_player,
    handle_player_disconnected,
    websocket_inout_resolve,
)
from backend.src.config import AppSettings
from backend.src.game.config.settings import DEBUG
from backend.src.game.utils.errors import GameLogicError

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
    cm: FromDishka[ConnectionManager],
):
    """
    Основная точка входа для WebSocket-соединения игры.

    Args:
        websocket: Экземпляр WebSocket соединения.
        game_id: ID игры, к которой подключается игрок.
        player_id: ID игрока, который подключается.
        gm: Экземпляр менеджера игр.
        cm: Экземпляр менеджера соединений.
    """

    logger.info(f"WebSocket: Checking player {player_id} in game {game_id}")

    try:
        game = await gm.get_player_game(player_id)
        if not game or game.game_id != game_id:
            reason = f"Игрок {player_id} не авторизован для игры {game_id} или игра не найдена."
            logger.warning(reason)
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=reason)
            return
    except PlayerNotInGameError:
        reason = f"Игрок {player_id} не найден ни в одной игре"
        logger.warning(reason)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=reason)
        return

    await cm.connect(player_id, websocket)
    logger.info(f"Игрок {player_id} подключился к игре {game_id}")

    # Уведомляем всех о подключении нового игрока
    await websocket_inout_resolve(
        {"type": "player_connected"}, game_id, player_id, game, websocket, cm, gm
    )
    try:
        while True:
            data = await websocket.receive_json()
            try:
                # Берем актуальное состояние игры перед ходом
                game = await gm.get_game_by_id(game_id)
                await websocket_inout_resolve(
                    data, game_id, player_id, game, websocket, cm, gm
                )
                # Сохраняем измененное состояние игры в Redis
                await gm.save_game(game)
            except GameLogicError as e:
                # Отправка специфичной ошибки игровой логики клиенту
                error_response = {
                    "type": MessageType.ERROR,
                    "data": {
                        "message": str(e),
                        "code": getattr(e, "error_code", "GAME_LOGIC_ERROR"),
                    },
                }
                logger.warning(f"Ошибка игровой логики для {player_id}: {e}")
                await websocket.send_json(error_response)
                # Повторная синхронизация состояния для клиента, вызвавшего ошибку
                await _send_full_game_state_to_player(game, player_id, cm)
            except Exception as e:
                # Отправка общей ошибки сервера
                logger.error(f"Неожиданная ошибка для {player_id}: {e}", exc_info=DEBUG)
                error_message = (
                    str(e) if DEBUG else "Произошла неожиданная ошибка на сервере."
                )
                error_code = e.__class__.__name__ if DEBUG else "UNEXPECTED_ERROR"
                await websocket.send_json(
                    {
                        "type": MessageType.ERROR,
                        "data": {"message": error_message, "code": error_code},
                    }
                )

    except WebSocketDisconnect:
        logger.info(f"Игрок {player_id} отключился от игры {game_id}")
        await handle_player_disconnected(game_id, player_id, game, cm, gm)
    except Exception as e:
        logger.error(
            f"Критическая ошибка WebSocket для {player_id}: {e}", exc_info=DEBUG
        )
    finally:
        await handle_player_disconnected(game_id, player_id, game, cm, gm)
        cm.disconnect(player_id)
        logger.info(f"Соединение для игрока {player_id} полностью закрыто.")
