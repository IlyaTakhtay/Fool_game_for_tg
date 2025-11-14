import json
import logging
from pydantic import ValidationError, parse_obj_as

from dishka import FromDishka
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from dishka.integrations.fastapi import inject

from backend.src.api.exceptions import PlayerNotInGameError
from backend.src.api.managers.game_manager import GameManager
from backend.src.api.managers.connection_managaer import ConnectionManager
from backend.src.api.models.websocket.data import GameOverData
from backend.src.api.models.websocket.enums import OutgoingMessageType
from backend.src.api.models.websocket.requests import IncomingMessage
from backend.src.api.models.websocket.responses import (
    GameOverResponse,
    PlayerGameStateResponse,
)
from backend.src.api.routers.websocket_handlers import (
    handle_player_disconnected,
    websocket_inout_resolve,
)
from backend.src.config import AppSettings
from backend.src.game.config.settings import DEBUG
from backend.src.game.utils.errors import GameLogicError
from backend.src.messaging.rabbitmq.subscription_manager import SubscriptionManager

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
    sm: FromDishka[SubscriptionManager],
):
    """
    Основная точка входа для WebSocket-соединения игры.

    Args:
        websocket: Экземпляр WebSocket соединения.
        game_id: ID игры, к которой подключается игрок.
        player_id: ID игрока, который подключается.
        gm: Экземпляр менеджера игр.
        cm: Экземпляр менеджера соединений.
        sm: Экземпляр менеджера подписок RabbitMQ.
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

    # Start consuming from the player's persistent queue
    async def message_handler(message_body: str):
        try:
            event_data = json.loads(message_body)
            routing_key = event_data.get("routing_key", "")

            if "state_changed" in routing_key or "player_joined" in routing_key:
                logger.debug(
                    f"Получено событие state_changed для {player_id}, запрашиваем полное состояние."
                )
                game = await gm.get_game_by_id(game_id)
                player_state = game.get_state_for_player(player_id)
                if player_state:
                    response = PlayerGameStateResponse(data=player_state)
                    try:
                        current_websocket = cm.get_connection(player_id)
                        if current_websocket:
                            await current_websocket.send_json(response.model_dump())
                        else:
                            logger.warning(
                                f"WebSocket для игрока {player_id} не найден в ConnectionManager на этом воркере. Возможно, подключен к другому воркеру."
                            )
                    except Exception as e:  # Catch broader exception for diagnosis
                        logger.error(
                            f"Ошибка при отправке state_changed через WebSocket для игрока {player_id}: {e}",
                            exc_info=DEBUG,
                        )
            elif "game_over" in routing_key:
                logger.debug(f"Получено событие game_over для {player_id}.")
                game_over_data = event_data.get("event", {})
                try:
                    current_websocket = cm.get_connection(player_id)
                    if current_websocket:
                        response = GameOverResponse(
                            data=GameOverData(
                                winner_id=game_over_data.get("winner_id"),
                                loser_ids=game_over_data.get("loser_ids"),
                            )
                        )
                        await current_websocket.send_json(response.model_dump())
                    else:
                        logger.warning(
                            f"WebSocket для игрока {player_id} не найден в ConnectionManager на этом воркере. Возможно, подключен к другому воркеру."
                        )
                except Exception as e:  # Catch broader exception for diagnosis
                    logger.error(
                        f"Ошибка при отправке game_over через WebSocket для игрока {player_id}: {e}",
                        exc_info=DEBUG,
                    )
            else:
                # For other events, just forward the raw data
                try:
                    current_websocket = cm.get_connection(player_id)
                    if current_websocket:
                        await current_websocket.send_text(message_body)
                    else:
                        logger.warning(
                            f"WebSocket для игрока {player_id} не найден в ConnectionManager на этом воркере. Возможно, подключен к другому воркеру."
                        )
                except Exception as e:  # Catch broader exception for diagnosis
                    logger.error(
                        f"Ошибка при отправке raw data через WebSocket для игрока {player_id}: {e}",
                        exc_info=DEBUG,
                    )

        except Exception as e:
            logger.error(
                f"Ошибка в message_handler для игрока {player_id}: {e}", exc_info=DEBUG
            )

    consumer_tag = await sm.start_consumer(player_id, message_handler)
    cm.set_player_subscription(player_id, consumer_tag)

    # Уведомляем всех о подключении нового игрока
    await websocket_inout_resolve(
        parse_obj_as(IncomingMessage, {"type": "player_connected"}),
        game_id,
        player_id,
        game,
        websocket,
        cm,
        gm,
    )
    try:
        while True:
            json_data = await websocket.receive_json()
            try:
                message = parse_obj_as(IncomingMessage, json_data)
                # Берем актуальное состояние игры перед ходом
                game = await gm.get_game_by_id(game_id)
                await websocket_inout_resolve(
                    message, game_id, player_id, game, websocket, cm, gm
                )
                # Сохраняем измененное состояние игры в Redis
                await gm.save_game(game)
            except ValidationError as e:
                error_response = {
                    "type": OutgoingMessageType.ERROR,
                    "data": {
                        "message": "Invalid message format",
                        "code": "VALIDATION_ERROR",
                        "details": e.errors(),
                    },
                }
                logger.warning(f"Ошибка валидации для {player_id}: {e}")
                await websocket.send_json(error_response)
            except GameLogicError as e:
                # Отправка специфичной ошибки игровой логики клиенту
                error_response = {
                    "type": OutgoingMessageType.ERROR,
                    "data": {
                        "message": str(e),
                        "code": getattr(e, "error_code", "GAME_LOGIC_ERROR"),
                    },
                }
                logger.warning(f"Ошибка игровой логики для {player_id}: {e}")
                await websocket.send_json(error_response)
                # Повторная синхронизация состояния для клиента, вызвавшего ошибку
                game = await gm.get_game_by_id(game_id)
                player_state = game.get_state_for_player(player_id)
                if player_state:
                    response = PlayerGameStateResponse(data=player_state)
                    await websocket.send_json(response.model_dump())
            except Exception as e:
                # Отправка общей ошибки сервера
                logger.error(f"Неожиданная ошибка для {player_id}: {e}", exc_info=DEBUG)
                error_message = (
                    str(e) if DEBUG else "Произошла неожиданная ошибка на сервере."
                )
                error_code = e.__class__.__name__ if DEBUG else "UNEXPECTED_ERROR"
                await websocket.send_json(
                    {
                        "type": OutgoingMessageType.ERROR,
                        "data": {"message": error_message, "code": error_code},
                    }
                )

    except WebSocketDisconnect:
        logger.info(f"Игрок {player_id} отключился от игры {game_id}")
    except Exception as e:
        logger.error(
            f"Критическая ошибка WebSocket для {player_id}: {e}", exc_info=DEBUG
        )
    finally:
        await handle_player_disconnected(game_id, player_id, game, cm, gm)
        # Stop consuming from RabbitMQ events (do not delete queue)
        consumer_tag_to_unsubscribe = cm.get_player_subscription(player_id)
        if consumer_tag_to_unsubscribe:
            await sm.stop_consumer(consumer_tag_to_unsubscribe)
        cm.disconnect(player_id)
        logger.info(f"Соединение для игрока {player_id} полностью закрыто.")
