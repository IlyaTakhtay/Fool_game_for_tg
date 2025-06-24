import logging

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status

from backend.api.dependencies import get_game_manager, connection_manager
from backend.api.managers.game_manager import GameManager
from backend.api.models.websocket_models import MessageType
from backend.api.routers.websocket_handlers import (
    _send_full_game_state_to_player,
    handle_player_disconnected,
    websocket_inout_resolve,
)
from backend.app.config.settings import DEBUG
from backend.app.utils.errors import GameLogicError

router = APIRouter(prefix="/api/v1", tags=["Games"])

logger = logging.getLogger(__name__)


@router.websocket("/ws/{game_id}")
async def websocket_game(
    websocket: WebSocket,
    game_id: str,
    player_id: str,
    gm: GameManager = Depends(get_game_manager),
):
    """
    Основная точка входа для WebSocket-соединения игры.

    Args:
        websocket: Экземпляр WebSocket соединения.
        game_id: ID игры, к которой подключается игрок.
        player_id: ID игрока, который подключается.
        gm: Экземпляр менеджера игр.
    """
    game = gm.get_game_by_player_id(player_id)
    if not game or game.game_id != game_id:
        reason = (
            f"Игрок {player_id} не авторизован для игры {game_id} или игра не найдена."
        )
        logger.warning(reason)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=reason)
        return

    await connection_manager.connect(player_id, websocket)
    logger.info(f"Игрок {player_id} подключился к игре {game_id}")

    # Уведомляем всех о подключении нового игрока
    await websocket_inout_resolve(
        {"type": "player_connected"}, game_id, player_id, game, websocket
    )

    try:
        while True:
            data = await websocket.receive_json()
            try:
                await websocket_inout_resolve(
                    data, game_id, player_id, game, websocket
                )
            except GameLogicError as e:
                # Отправка специфичной ошибки игровой логики клиенту
                error_response = {
                    "type": MessageType.ERROR,
                    "data": {"message": str(e), "code": getattr(e, "error_code", "GAME_LOGIC_ERROR")},
                }
                logger.warning(f"Ошибка игровой логики для {player_id}: {e}")
                await websocket.send_json(error_response)
                # Повторная синхронизация состояния для клиента, вызвавшего ошибку
                await _send_full_game_state_to_player(game, player_id)
            except Exception as e:
                # Отправка общей ошибки сервера
                logger.error(f"Неожиданная ошибка для {player_id}: {e}", exc_info=DEBUG)
                error_message = str(e) if DEBUG else "Произошла неожиданная ошибка на сервере."
                error_code = e.__class__.__name__ if DEBUG else "UNEXPECTED_ERROR"
                await websocket.send_json(
                    {
                        "type": MessageType.ERROR,
                        "data": {"message": error_message, "code": error_code},
                    }
                )

    except WebSocketDisconnect:
        logger.info(f"Игрок {player_id} отключился от игры {game_id}")
        await handle_player_disconnected(game_id, player_id, game)
    except Exception as e:
        logger.error(f"Критическая ошибка WebSocket для {player_id}: {e}", exc_info=DEBUG)
    finally:
        connection_manager.disconnect(player_id)
        logger.info(f"Соединение для игрока {player_id} полностью закрыто.") 