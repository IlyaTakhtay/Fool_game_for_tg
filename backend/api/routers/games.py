import logging
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse

from backend.api.dependencies import get_game_manager
from backend.api.managers.game_manager import GameManager
from backend.api.models.game import (
    GameCreatedResponse,
    GameInfoResponse,
    GameJoinedResponse,
)
from backend.app.contracts.game_contract import ActionResult, PlayerAction, PlayerInput
from backend.app.models.game import FoolGame
from backend.app.config.settings import DEBUG

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Games"])


@router.post(
    "/create_game",
    response_model=GameCreatedResponse,
    summary="Создать новую игру",
    description="Создает новую игровую комнату с указанным лимитом игроков.",
)
async def create_game(
    set_players_limit: int = 2, gm: GameManager = Depends(get_game_manager)
) -> GameCreatedResponse:
    """Создает новую игру.

    Args:
        set_players_limit: Максимальное количество игроков для игры.
        gm: Экземпляр менеджера игр.

    Returns:
        Объект GameCreatedResponse с ID игры и лимитом игроков.

    Raises:
        HTTPException: Если лимит игроков не находится в диапазоне от 2 до 6.
    """
    if not (2 <= set_players_limit <= 6):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Количество игроков должно быть от 2 до 6.",
        )

    game = gm.create_game(set_players_limit)
    return GameCreatedResponse(game_id=game.game_id, players_limit=set_players_limit)


@router.post(
    "/join_game",
    response_model=GameJoinedResponse,
    summary="Присоединиться к игре",
    description="Присоединяет игрока к существующей или новой игре. Если game_id не указан, находит доступную игру.",
)
async def join_game(
    player_id: str,
    game_id: str | None = None,
    gm: GameManager = Depends(get_game_manager),
) -> GameJoinedResponse:
    """Присоединяет игрока к игре.

    Args:
        player_id: ID присоединяющегося игрока.
        game_id: ID игры для присоединения. Если None, находит доступную игру.
        gm: Экземпляр менеджера игр.

    Returns:
        Объект GameJoinedResponse с деталями игры и игрока.

    Raises:
        HTTPException: Если игра не найдена, заполнена, или если игрок уже в игре.
    """
    if game_id:
        game = gm.get_game_by_id(game_id)
        if not game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Игра с ID {game_id} не найдена.",
            )
        if player_id in [p.id_ for p in game.players]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Вы уже в этой игре."
            )
    else:
        game = gm.find_available_game() or gm.create_game(players_limit=2)
        game_id = game.game_id

    player_input = PlayerInput(player_id=player_id, action=PlayerAction.JOIN)

    try:
        answer = game.handle_input(player_input)
        if answer.result != ActionResult.SUCCESS:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=answer.message
            )
    except Exception as e:
        logger.error(f"Ошибка присоединения к игре: {e}", exc_info=DEBUG)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

    gm.add_game_to_player(game_id, player_id)
    gm.update_game_slots_by_id(game_id)
    # TODO: сделать env для исправления жестко закодированного пути к серверу
    return GameJoinedResponse(
        game_id=game.game_id,
        player_id=player_id,
        websocket_connection=f"ws://localhost:8000/api/v1/ws/{game_id}?player_id={player_id}",
    )


@router.post("/exit_game", summary="Выйти из игры")
async def exit_game(
    player_id: str, gm: GameManager = Depends(get_game_manager)
) -> JSONResponse:
    """Удаляет игрока из игры.

    Args:
        player_id: ID удаляемого игрока.
        gm: Экземпляр менеджера игр.

    Returns:
        JSONResponse с сообщением об успехе.

    Raises:
        HTTPException: Если игрок не найден ни в одной игре.
    """
    game: FoolGame = gm.get_game_by_player_id(player_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Игрок с ID {player_id} не найден ни в одной игре.",
        )

    gm.handle_player_quit(game.game_id, player_id)

    return JSONResponse(content={"message": "Успешный выход из игры"})


@router.get("/player_game", response_model=GameInfoResponse, summary="Получить активную игру игрока")
async def active_game(
    player_id: str, gm: GameManager = Depends(get_game_manager)
) -> GameInfoResponse:
    """Получает активную игру для игрока.

    Args:
        player_id: ID игрока.
        gm: Экземпляр менеджера игр.

    Returns:
        Объект GameInfoResponse с деталями игры игрока.

    Raises:
        HTTPException: Если игрок не найден ни в одной игре.
    """
    game = gm.get_game_by_player_id(player_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Игрок с ID {player_id} не найден ни в одной игре.",
        )
    return GameInfoResponse(
        game_id=game.game_id,
        players_limit=game.players_limit,
        players_inside=len(game.players),
        websocket_connection=f"ws://localhost:8000/api/v1/ws/{game.game_id}?player_id={player_id}",
    )


@router.get(
    "/games",
    response_model=list[GameInfoResponse],
    summary="Список доступных игр",
    description="Показывает список игр, которые еще не заполнены.",
)
def get_games(gm: GameManager = Depends(get_game_manager)) -> list[GameInfoResponse]:
    """Получает список доступных игр.

    Args:
        gm: Экземпляр менеджера игр.

    Returns:
        Список объектов GameInfoResponse.
    """
    games: list[GameInfoResponse] = []
    for game in gm.flatten_pending_games:
        game_info = GameInfoResponse(
            game_id=game.game_id,
            players_limit=game.players_limit,
            players_inside=len(game.players),
        )
        games.append(game_info)
    return games
