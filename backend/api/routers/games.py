from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi import status

from backend.api.managers.connection_managaer import ConnectionManager
from backend.api.managers.game_manager import GameManager
from backend.api.models.game import GameCreatedResponse, GameInfoListResponse, GameInfoResponse, GameJoinedResponse
from backend.app.contracts.game_contract import ActionResult, PlayerAction, PlayerInput
from backend.app.models.game import FoolGame
from backend.app.utils.logger import setup_logger

router = APIRouter(prefix="/api/v1", tags=["Games"])
game_manager_instance: GameManager = GameManager()
connection_manager_instance: ConnectionManager = ConnectionManager()
logger = setup_logger(name = "api_logger")

def get_comm_manager() -> GameManager:
    """
    Возвращает экземпляр GameManager.
    """
    return game_manager_instance

#TODO: убрать создание новой игры и сделать лонг polling ответ пока не найдется игра
@router.post(
    "/games",
    response_model=GameCreatedResponse,
    summary="Создать новую игру",
    description="Создает новую игровую комнату с указанным лимитом игроков."
)
async def create_game(
    set_players_limit: int = 2,
    gm: GameManager = Depends(get_comm_manager)
):
    if set_players_limit < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Минимальное количество игроков — 2."
        )
    elif set_players_limit > 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Максимальное количество игроков — 6."
        )
    
    game = gm.create_game(set_players_limit)
    return GameCreatedResponse(game_id=game.game_id, players_limit=set_players_limit)

@router.post(
    "/join",
    response_model=GameJoinedResponse,
    summary="Присоединиться к игре",
    description="""Присоединяет игрока к существующей или новой игре.
    Если game_id не указан, система автоматически находит доступную игру.""",
    responses={
        200: {"description": "Успешное присоединение к игре"},
        404: {"description": "Игра не найдена"},
        409: {"description": "Игра заполнена"},
        422: {"description": "Некорректные данные игрока"}
    }
)
async def join_game(
    player_name: str,
    game_id: str | None = None,
    gm: GameManager = Depends(get_comm_manager)
):
    # Валидация имени игрока
    if not (2 <= len(player_name) <= 20):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Имя игрока должно содержать от 2 до 20 символов"
        )

    # Поиск или создание игры
    if game_id:
        game = gm.get_game_by_id(game_id)
        if not game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Игра с указанным ID не найдена"
            )
    else:
        game = gm.find_available_game() or gm.create_game(players_limit=2)
        game_id = game.game_id
    # Генерация временного ID (TODO: заменить на систему аутентификации)
    player_id = str(uuid4())

    # Создание и обработка игрового действия
    player_input = PlayerInput(
        player_id=player_id,
        action=PlayerAction.JOIN,
    )
    
    try:
        answer = game.handle_input(player_input)
    except Exception as e:
        # Логирование ошибки для дебаггинга
        logger.error(f"Ошибка присоединения к игре: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )
    # Обработка результатов
    if answer.result == ActionResult.ROOM_FULL:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=answer.message
        )
    elif answer.result == ActionResult.INVALID_ACTION:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=answer.message
        )
    
    gm.update_game_slots_by_id(game_id)
    return GameJoinedResponse(
        game_id=game.game_id,
        player_id=player_id,
        player_name=player_name,
        #TODO: make env to fix serverpath
        websocket_connection=f"ws://localhost:8000/api/v1/ws/{game_id}?player_id={player_id}",
    )

#TODO: параметры сортировки, фильтрации и т.д.
@router.get("/games",
            response_model=list[GameInfoResponse],
            summary="Cписок игр",
            description="""Показвает список еще не заполненных игр.""")
def get_games():
    games: list[GameInfoResponse] = list() 
    for game in game_manager_instance.flatten_pending_games:
        game: FoolGame
        game_info = GameInfoResponse(
            game_id=game.game_id,
            players_limit=game.players_limit, 
            players_inside=len(game.players)
            )
        games.append(game_info)
    return games


@router.websocket("/ws/{game_id}")
async def websocket_game(
    websocket: WebSocket,
    game_id: str,
    gm: GameManager = Depends(get_comm_manager)
):
    # Проверяем валидность игры и игрока
    game = gm.get_game_by_id(game_id)
    await websocket.accept()
    if not game:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    player_id = websocket.query_params.get("player_id")
    if player_id not in [p.id_ for p in game.players]:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Регистрируем соединение в менеджере
    connection_manager_instance.connect(game_id, player_id, websocket)
    
    try:
        while True:
            # Ожидаем сообщения от клиента (можно использовать для игровых действий)
            data = await websocket.receive_text()
            logger.info(f"Received WebSocket message: {data}")
            
    except WebSocketDisconnect:
        # Удаляем соединение при отключении
        connection_manager_instance.remove_connection(game_id, player_id)
        logger.info(f"Player {player_id} disconnected from game {game_id}")
