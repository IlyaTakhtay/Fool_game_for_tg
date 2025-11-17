import logging
from uuid import uuid4
from dishka import FromDishka
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from dishka.integrations.fastapi import DishkaRoute

from backend.src.api.exceptions import (
    GameNotFoundError,
    PlayerAlreadyInGameError,
    PlayerNotInGameError,
)
from backend.src.api.managers.game_manager import GameManager
from backend.src.api.models.game import (
    GameCreatedResponse,
    GameInfoResponse,
    GameJoinedResponse,
)
from backend.src.config import AppSettings, WebSocketSettings
from backend.src.game.contracts.game_contract import (
    ActionResult,
    PlayerAction,
    PlayerInput,
)
from backend.src.game.models.game import FoolGame
from backend.src.game.utils.errors import GameLogicError

logger = logging.getLogger(__name__)
ws_settings = WebSocketSettings()
app_settings = AppSettings()

router = APIRouter(
    prefix=f"/api/{app_settings.api_version_prefix}",
    tags=["Games"],
    route_class=DishkaRoute,
)


@router.post(
    "/create_game",
    summary="Создать новую игру",
    response_model=GameCreatedResponse,
    description="Создает новую игровую комнату с указанным лимитом игроков.",
)
async def create_game(
    gm: FromDishka[GameManager],
    set_players_limit: int = 2,
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

    game = await gm.create_game(set_players_limit)
    return GameCreatedResponse(game_id=game.game_id)


@router.post(
    "/join_game",
    response_model=GameJoinedResponse,
    summary="Присоединиться к игре",
    description="Присоединяет игрока к существующей или новой игре. Если game_id не указан, находит доступную игру.",
)
async def join_game(
    gm: FromDishka[GameManager],
    player_id: str,
    game_id: str | None = None,
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
    game = None
    try:
        game = await gm.join_game(player_id, game_id)
    except GameNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except GameLogicError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка присоединения: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

    return GameJoinedResponse(
        game_id=game.game_id,
        player_id=player_id,
        websocket_connection=f"{ws_settings.base_url}/api/{app_settings.api_version_prefix}/ws/{game.game_id}?player_id={player_id}",
        game_state=game.get_game_state(),
    )


@router.post("/exit_game", summary="Выйти из игры")
async def exit_game(
    gm: FromDishka[GameManager],
    player_id: str,
) -> None:
    """Удаляет игрока из игры.

    Args:
        player_id: ID удаляемого игрока.
        gm: Экземпляр менеджера игр.

    Returns:
        None

    Raises:
        HTTPException: Если игрок не найден ни в одной игре.
    """
    try:
        await gm.exit_game(player_id)
    except PlayerNotInGameError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except GameLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Ошибка выхода из игры: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера",
        )


@router.get(
    "/player_game",
    response_model=GameInfoResponse,
    summary="Получить активную игру игрока",
)
async def active_game(
    gm: FromDishka[GameManager],
    player_id: str,
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
    try:
        game = await gm.get_player_game(player_id)
    except PlayerNotInGameError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    return GameInfoResponse(
        game_id=game.game_id,
        players_limit=game.players_limit,
        players_inside=len(game.players),
        websocket_connection=f"{ws_settings.base_url}/api/{app_settings.api_version_prefix}/ws/{game.game_id}?player_id={player_id}",
    )


@router.get(
    "/games",
    response_model=list[GameInfoResponse],
    summary="Список доступных игр",
    description="Показывает список игр, которые еще не заполнены.",
)
async def get_games(
    gm: FromDishka[GameManager],
    limit: int = 100,
    offset: int = 0,
) -> list[GameInfoResponse]:
    """Получает список доступных игр.

    Args:
        gm: Экземпляр менеджера игр.

    Returns:
        Список объектов GameInfoResponse.
    """
    games = await gm.get_pending_games(limit, offset)
    return [
        GameInfoResponse(
            game_id=game.game_id,
            players_limit=game.players_limit,
            players_inside=len(game.players),
        )
        for game in games
    ]
