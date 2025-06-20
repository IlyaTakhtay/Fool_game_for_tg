from uuid import uuid4
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Request,
)
from fastapi import status
import json
import asyncio
from sse_starlette.sse import EventSourceResponse
from fastapi.responses import JSONResponse
import hashlib
import ast

from backend.api.managers.connection_managaer import ConnectionManager
from backend.api.managers.game_manager import GameManager
from backend.api.models.game import (
    GameCreatedResponse,
    GameInfoListResponse,
    GameInfoResponse,
    GameJoinedResponse,
)
from backend.api.models.websocket_models import (
    PrivatePlayerData,
    PlayerConnectionResponse,
    MessageType,
    PlayerDisconnectedData,
    PlayerDisconnectedResponse,
    PublicPlayerData,
    PlayerJoinedResponse,
    PlayerStatusChangedResponse,
    PlayerStatusData,
    ReconnectionData,
    ReconnectionResponse,
    CardPlayedResponse,
)
from backend.app.contracts.game_contract import (
    ActionResult,
    PlayerAction,
    PlayerInput,
    StateTransition,
)
from backend.app.models.game import FoolGame
from backend.app.models.player import Player, PlayerStatus
from backend.app.utils.logger import setup_logger
from backend.app.models.card import Card

router = APIRouter(prefix="/api/v1", tags=["Games"])
game_manager_instance: GameManager = GameManager()
connection_manager_instance: ConnectionManager = ConnectionManager()
logger = setup_logger(name="api_logger")


def get_comm_manager() -> GameManager:
    """
    Возвращает экземпляр GameManager.
    """
    return game_manager_instance


# TODO: убрать создание новой игры и сделать лонг polling ответ пока не найдется игра
# TODO: переименовать машршруты на /game/create /game/join /game/exit
@router.post(
    "/create_game",
    response_model=GameCreatedResponse,
    summary="Создать новую игру",
    description="Создает новую игровую комнату с указанным лимитом игроков.",
)
async def create_game(
    set_players_limit: int = 2, gm: GameManager = Depends(get_comm_manager)
):
    if set_players_limit < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Минимальное количество игроков — 2.",
        )
    elif set_players_limit > 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Максимальное количество игроков — 6.",
        )

    game = gm.create_game(set_players_limit)
    return GameCreatedResponse(game_id=game.game_id, players_limit=set_players_limit)


@router.post(
    "/join_game",
    response_model=GameJoinedResponse,
    summary="Присоединиться к игре",
    description="""Присоединяет игрока к существующей или новой игре.
    Если game_id не указан, система автоматически находит доступную игру.""",
    responses={
        200: {"description": "Успешное присоединение к игре"},
        404: {"description": "Игра не найдена"},
        409: {"description": "Игра заполнена"},
        422: {"description": "Некорректные данные игрока"},
    },
)
async def join_game(
    player_id: str,
    game_id: str | None = None,
    gm: GameManager = Depends(get_comm_manager),
):
    # заменить player_id на токены (TODO: заменить на систему аутентификации)
    # Поиск или создание игры
    if game_id:
        game = gm.get_game_by_id(game_id)
        if not game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Игра с указанным ID не найдена",
            )
        if player_id in [
            p.id_ for p in game.players
        ]:  # Проверка существующего игрока
            raise HTTPException(status_code=409, detail="Вы уже подключились")
    else:
        game = gm.find_available_game() or gm.create_game(players_limit=2)
        game_id = game.game_id

    # Создание и обработка игрового действия
    player_input = PlayerInput(
        player_id=player_id,
        action=PlayerAction.JOIN,
    )

    try:
        answer = game.handle_input(player_input)
        if answer.result == ActionResult.ROOM_FULL:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=answer.message
            )
        elif answer.result == ActionResult.INVALID_ACTION:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=answer.message
            )
        elif answer.result != ActionResult.SUCCESS:
            logger.error(f"Ошибка присоединения к игре: {answer.message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=answer.message
            )
    except Exception as e:
        logger.error(f"Ошибка присоединения к игре: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    gm.add_game_to_player(game_id, player_id)
    gm.update_game_slots_by_id(game_id)
    return GameJoinedResponse(
        game_id=game.game_id,
        player_id=player_id,
        # TODO: make env to fix hardcoded serverpath
        websocket_connection=f"ws://localhost:8000/api/v1/ws/{game_id}?player_id={player_id}",
    )


@router.post("/exit_game")
async def exit_game(player_id: str, gm: GameManager = Depends(get_comm_manager)):
    # Удаляем игрока из игры
    game: FoolGame = gm.get_game_by_player_id(player_id)
    logger.debug(
        f"Player with id: {player_id} will be removed from game with id: {game.game_id}"
    )
    if game:
        # Удаляем игрока из игры
        game.players = [p for p in game.players if p.id_ != player_id]

        # Обновляем состояние игры
        gm.update_game_slots_by_id(game.game_id)

        # Удаляем связь игрока с игрой
        gm.remove_game_from_player(player_id)

        return {"message": "Successfully exited the game"}
    else:
        raise HTTPException(status_code=404, detail="Player not found in any game")


@router.get("/player_game")
async def active_game(player_id: str, gm: GameManager = Depends(get_comm_manager)):
    game = gm.get_game_by_player_id(player_id)
    if game is not None:
        return GameInfoResponse(
            game_id=game.game_id,
            players_limit=game.players_limit,
            players_inside=len(game.players),
            # TODO: make env to fix hardcoded serverpath
            websocket_connection=f"ws://localhost:8000/api/v1/ws/{game.game_id}?player_id={player_id}",
        )
    else:
        raise HTTPException(
            status_code=404, detail=f"Игрок с ID {player_id} не найден ни в одной игре."
        )


# TODO: добавить параметры сортировки, фильтрации и т.д.
@router.get(
    "/games",
    response_model=list[GameInfoResponse],
    summary="Cписок игр",
    description="""Показвает список еще не заполненных игр.""",
)
def get_games():
    games: list[GameInfoResponse] = list()
    for game in game_manager_instance.flatten_pending_games:
        game: FoolGame
        game_info = GameInfoResponse(
            game_id=game.game_id,
            players_limit=game.players_limit,
            players_inside=len(game.players),
        )
        games.append(game_info)
    return games


def get_games_list() -> list[dict]:
    """Вспомогательная функция для получения списка игр в нужном формате"""
    games = []
    for game in game_manager_instance.flatten_pending_games:
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
    Server-Sent Events endpoint для получения обновлений списка игр.
    Отправляет обновления каждые 3 секунды или пинг каждые 30 секунды.
    Прекращает отправку, если игрок уже находится в игре.

    Отправляет обновления в формате:
    event: games_update
    data: [{"game_id": "...", "players_limit": N, "players_inside": M}, ...]

    Или пинг каждые 30 секунд:
    event: ping
    data: ""
    """
    # Получаем player_id из query параметров
    player_id = request.query_params.get("player_id")
    logger.debug(f"SSE connection attempt - Query params: {dict(request.query_params)}")
    logger.debug(f"SSE connection attempt - Player ID: {player_id}")

    if not player_id:
        logger.warning("SSE connection rejected - Missing player_id parameter")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="player_id is required"
        )

    # Проверяем валидность player_id
    if not isinstance(player_id, str) or not player_id.strip():
        logger.warning(
            f"SSE connection rejected - Invalid player_id format: {player_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid player_id format"
        )

    logger.info(f"SSE connection accepted for player_id: {player_id}")

    async def event_generator():
        last_games = None
        ping_counter = 0

        try:
            while True:
                if await request.is_disconnected():
                    logger.debug(
                        f"Client disconnected from SSE stream (player_id: {player_id})"
                    )
                    break

                # Проверяем, не находится ли игрок уже в игре
                current_game = game_manager_instance.get_game_by_player_id(player_id)
                if current_game:
                    logger.debug(
                        f"Player {player_id} is already in game {current_game.game_id}, stopping SSE updates"
                    )
                    # Отправляем специальное событие закрытия
                    yield {"event": "close", "data": "Player joined game"}
                    break

                # Получаем текущий список игр
                current_games = get_games_list()

                # Если список игр изменился или прошло 10 пингов без обновлений
                if current_games != last_games or ping_counter >= 10:
                    logger.debug(
                        f"Sending games update to player {player_id}: {len(current_games)} games"
                    )
                    yield {"event": "games_update", "data": json.dumps(current_games)}
                    last_games = current_games
                    ping_counter = 0
                else:
                    # Отправляем пинг каждые 30 секунд
                    logger.debug(f"Sending ping to player {player_id}")
                    yield {"event": "ping", "data": ""}
                    ping_counter += 1

                # Ждем 3 секунды перед следующей проверкой
                await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"Error in SSE stream for player {player_id}: {str(e)}")
            raise
        finally:
            logger.debug(f"SSE stream closed for player {player_id}")

    return EventSourceResponse(event_generator())


async def websocket_inout_resolve(
    data: dict, game_id: str, player_id: str, game: FoolGame, websocket: WebSocket
) -> None:
    message_type = data.get("type")
    message_data = data.get("data")
    logger.info(
        f"Received WebSocket message from player {player_id} in game {game_id}: type={message_type}, data={message_data}"
    )

    try:
        match message_type:
            case "player_connected":
                logger.info(
                    f"Handling player_connected for player {player_id} in game {game_id}"
                )
                await handle_player_connected(game_id, player_id, game, websocket)

            case "player_disconnected":
                logger.info(
                    f"Handling player_disconnected for player {player_id} in game {game_id}"
                )
                await handle_player_disconnected(game_id, player_id, game)

            case "change_status":
                new_status = message_data.get("status")
                logger.info(
                    f"Handling change_status for player {player_id} in game {game_id}: new_status={new_status}"
                )
                await handle_player_status_changed(game_id, player_id, new_status, game)

            case "play_card":
                await handle_play_card(game_id, player_id, game, websocket, data)
            
            case _:
                logger.warning(
                    f"Unknown message type: {message_type} from player {player_id} in game {game_id}"
                )
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        # Re-raise the exception to be handled by the main WebSocket handler
        raise


async def handle_player_connected(
    game_id: str, player_id: str, game: FoolGame, websocket: WebSocket
):
    """Обработка подключения игрока"""

    player: Player = next((p for p in game.players if p.id_ == player_id), None)
    if not player:
        logger.warning(f"Игрок {player_id} не найден в игре {game_id}")
        return

    logger.debug(f"All players in game: {[p.id_ for p in game.players]}")
    logger.debug(f"Current player: {player_id}")
    logger.debug(
        f"Other players: {[p.id_ for p in game.players if p.id_ != player_id]}"
    )

    # Отправляем полное состояние игры
    full_state_response = ReconnectionResponse(
        data=ReconnectionData(
            # PrivatePlayerData
            status=player.status,
            position=game.get_player_position(player_id),
            cards=[card.to_dict() for card in player.get_cards()],
            # PublicGameData
            room_size=game.players_limit,
            room_players=[
                PublicPlayerData(
                    player_id=p.id_,
                    position=game.get_player_position(p.id_),
                    cards_count=len(p.get_cards()),
                    status=getattr(p, "status", PlayerStatus.UNREADY),
                    name=p.name,
                )
                for p in game.players
                if p.id_ != player_id
            ],
            deck_size=len(game.deck),
            trump_suit=game.deck.trump_suit,
            trump_rank=game.deck.trump_card.rank,
            attacker_position=(
                game.get_player_position(game.current_attacker_id)
                if game.current_attacker_id
                else -1
            ),
            defender_position=(
                game.get_player_position(game.current_defender_id)
                if game.current_defender_id
                else -1
            ),
            table_cards=[card.to_dict() for card in game.game_table.table_cards],
        )
    )

    await websocket.send_json(full_state_response.model_dump())

    # Уведомляем других игроков о новом игроке
    player_joined_response = PlayerJoinedResponse(
        data=PublicPlayerData(
            player_id=player_id,
            position=game.get_player_position(player_id),
            cards_count=len(player.get_cards()),
            status=player.status,
            name=player.name,
        )
    )

    other_player_ids = [p.id_ for p in game.players if p.id_ != player_id]
    await connection_manager_instance.broadcast_to_players(
        other_player_ids, player_joined_response.model_dump()
    )


async def handle_player_disconnected(game_id: str, player_id: str, game: FoolGame):
    """Обработка отключения игрока"""

    # Обрабатываем выход игрока через GameManager
    game_manager_instance.handle_player_quit(game_id, player_id)

    # Уведомляем всех остальных игроков
    disconnect_response = PlayerDisconnectedResponse(
        data=PlayerDisconnectedData(
            player_id=player_id,
        )
    )

    other_player_ids = [p.id_ for p in game.players]
    await connection_manager_instance.broadcast_to_players(
        other_player_ids, disconnect_response.model_dump()
    )


async def handle_player_status_changed(
    game_id: str, player_id: str, new_status: str, game: FoolGame
):
    """Обработка изменения статуса игрока"""
    try:
        if not game:
            logger.error(f"Game {game_id} not found")
            return

        player: Player = game.get_player_by_id(player_id=player_id)
        if not player:
            logger.error(f"Player {player_id} not found in game {game_id}")
            return

        # Обновляем статус игрока
        action = PlayerAction.READY if new_status == "ready" else PlayerAction.UNREADY
        response = game.handle_input(
            player_input=PlayerInput(
                player_id=player_id,
                action=action,
            )
        )

        # Подробное логирование ответа
        logger.debug(f"Response type: {type(response)}")
        logger.debug(f"Response content: {response}")
        logger.debug(f"Response dir: {dir(response)}")

        if isinstance(response, StateTransition):
            logger.info(
                f"State transition detected, sending full game state to all players"
            )
            # Отправляем полное состояние игры всем игрокам
            for p in game.players:
                full_state_response = ReconnectionResponse(
                    data=ReconnectionData(
                        # PrivatePlayerData
                        status=p.status,
                        position=game.get_player_position(p.id_),
                        cards=[card.to_dict() for card in p.get_cards()],
                        # PublicGameData
                        room_size=game.players_limit,
                        room_players=[
                            PublicPlayerData(
                                player_id=other_p.id_,
                                position=game.get_player_position(other_p.id_),
                                cards_count=len(other_p.get_cards()),
                                status=getattr(other_p, "status", PlayerStatus.UNREADY),
                                name=other_p.name,
                            )
                            for other_p in game.players
                            if other_p.id_ != p.id_
                        ],
                        deck_size=len(game.deck),
                        trump_suit=game.deck.trump_suit,
                        trump_rank=game.deck.trump_card.rank,
                        attacker_position=(
                            game.get_player_position(game.current_attacker_id)
                            if game.current_attacker_id
                            else -1
                        ),
                        defender_position=(
                            game.get_player_position(game.current_defender_id)
                            if game.current_defender_id
                            else -1
                        ),
                        table_cards=[
                            card.to_dict() for card in game.game_table.table_cards
                        ],
                    )
                )
                await connection_manager_instance.send_message(
                    p.id_, full_state_response.model_dump()
                )
            return

        if response.result != ActionResult.SUCCESS:
            logger.error(
                f"Failed to change player status: {response.result}, {response.message}"
            )
            raise Exception(response.message)

        # Создаем сообщение об изменении статуса
        status_response = PlayerStatusChangedResponse(
            data=PlayerStatusData(player_id=player_id, status=new_status)
        )
        response_data = status_response.model_dump()

        # Отправляем всем игрокам, включая текущего
        all_player_ids = [p.id_ for p in game.players]
        await connection_manager_instance.broadcast_to_players(
            all_player_ids, response_data
        )

        logger.info(
            f"Player {player_id} status changed to {new_status} in game {game_id}"
        )

    except Exception as e:
        logger.error(f"Error handling player status change: {str(e)}", exc_info=True)
        # Не закрываем соединение здесь, пусть это решает основной обработчик WebSocket


@router.websocket("/ws/{game_id}")
async def websocket_game(
    websocket: WebSocket, game_id: str, gm: GameManager = Depends(get_comm_manager)
):
    # Проверяем валидность игры и игрока
    game = gm.get_game_by_id(game_id)
    if not game:
        logger.warning(f"Игра {game_id} не найдена")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    player_id = websocket.query_params.get("player_id")
    if not player_id or player_id not in [p.id_ for p in game.players]:
        logger.warning(f"Игрок {player_id} не найден в игре {game_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Регистрируем соединение
    await connection_manager_instance.connect(player_id, websocket)
    logger.info(f"Игрок {player_id} подключен к игре {game_id}")

    try:
        while True:
            # Ожидаем сообщения от клиента
            data = await websocket.receive_json()
            logger.info(
                f"Raw WebSocket message received from player {player_id} in game {game_id}: {data}"
            )

            await websocket_inout_resolve(data, game_id, player_id, game, websocket)

    except WebSocketDisconnect:
        # Удаляем соединение при отключении
        connection_manager_instance.disconnect(player_id)
        logger.info(f"Игрок {player_id} отключен от игры {game_id}")

        # Уведомляем других игроков об отключении
        await handle_player_disconnected(game_id, player_id, game)
    except Exception as e:
        logger.error(f"WebSocket error for player {player_id} in game {game_id}: {e}")
        connection_manager_instance.disconnect(player_id)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


async def handle_play_card(
    game_id: str, player_id: str, game: FoolGame, websocket: WebSocket, data: dict
):
    card_data = data.get("attack_card")
    if not card_data:
        raise HTTPException(status_code=400, detail="attack_card is required")

    defend_card_data = data.get("defend_card")

    # Логируем только базовую информацию о ходе
    logger.info(f"handle_play_card: player_id={player_id}, attack_card={card_data}, defend_card={defend_card_data}")
    player = game.get_player_by_id(player_id)
    if player:
        logger.info(f"Карты игрока {player_id} ДО хода: {[str(c) for c in player.get_cards()]}")
    else:
        logger.warning(f"Игрок {player_id} не найден для логирования карт")

    trump_suit = game.deck.trump_suit
    if defend_card_data:
        action = PlayerAction.DEFEND
        player_input = PlayerInput(
            player_id=player_id,
            action=action,
            attack_card=Card.from_dict(card_data, trump_suit=trump_suit),
            defend_card=Card.from_dict(defend_card_data, trump_suit=trump_suit)
        )
    else:
        action = PlayerAction.ATTACK
        player_input = PlayerInput(
            player_id=player_id,
            action=action,
            attack_card=Card.from_dict(card_data, trump_suit=trump_suit)
        )

    logger.info(f"Тип карты для хода: {type(player_input.attack_card)} {player_input.attack_card}")

    try:
        answer = game.handle_input(player_input)
        # Логируем карты игрока после хода
        if player:
            logger.info(f"Карты игрока {player_id} ПОСЛЕ хода: {[str(c) for c in player.get_cards()]}")
        if answer.result == ActionResult.ROOM_FULL:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=answer.message
            )
        elif answer.result == ActionResult.INVALID_ACTION:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=answer.message
            )
        elif answer.result != ActionResult.SUCCESS:
            logger.error(f"Ошибка при выполнении хода: {answer.message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=answer.message
            )
    except Exception as e:
        logger.error(f"Ошибка при выполнении хода: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    # Сериализация карт в answer.data перед отправкой
    data = answer.data.copy() if answer.data else {}
    # Сериализуем attack_card/defend_card если есть
    if "attack_card" in data and hasattr(data["attack_card"], "to_dict"):
        data["attack_card"] = data["attack_card"].to_dict()
    if "defend_card" in data and hasattr(data["defend_card"], "to_dict"):
        data["defend_card"] = data["defend_card"].to_dict()
    # Сериализуем table_cards если есть
    if "table_cards" in data:
        def serialize_card_pair(pair):
            # Если это строка, парсим в dict
            if isinstance(pair, str):
                try:
                    pair = ast.literal_eval(pair)
                except Exception:
                    return pair
            if isinstance(pair, dict):
                def ser(card):
                    if hasattr(card, "to_dict"):
                        return card.to_dict()
                    return card
                return {
                    "attack_card": ser(pair.get("attack_card")),
                    "defend_card": ser(pair.get("defend_card")),
                }
            return pair
        data["table_cards"] = [serialize_card_pair(pair) for pair in data["table_cards"]]

    response = CardPlayedResponse(
        data=data,
        type=MessageType.CARD_PLAYED,
    )
    response_json = response.model_dump()
    logger.info(f"WEBSOCKET SEND CARD_PLAYED: game_id={game_id}, player_id={player_id}, response_json={response_json}")
    await websocket.send_json(response_json)

    # Уведомляем других игроков о ходе
    other_player_ids = [p.id_ for p in game.players if p.id_ != player_id]
    await connection_manager_instance.broadcast_to_players(
        other_player_ids, response.model_dump()
    )

    logger.info(f"Ход {player_id} в игре {game_id} выполнен успешно")
