import uuid
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi import status, Request

from backend.api.managers.connection_managaer import ConnectionManager
from backend.api.managers.game_manager import GameManager
from backend.api.models.game import GameCreatedResponse, GameInfoListResponse, GameInfoResponse, GameJoinedResponse
from backend.api.models.player import ResponsePlayer
from backend.app.contracts.game_contract import ActionResult, PlayerAction, PlayerInput
from backend.app.models.game import FoolGame
from backend.app.utils.logger import setup_logger

logger = setup_logger(name="auth_logger", log_file="logs/auth.log")
router = APIRouter(prefix="/api/v1", tags=["Auth"])

@router.post('/auth_guest', response_model=ResponsePlayer)
async def auth_guest(request: Request, player_name: str):
    """
    Эндпоинт для авторизации гостя.
    Генерирует уникальный ID игрока и возвращает его.
    """
    logger.info(f"Получен запрос на авторизацию гостя. Headers: {dict(request.headers)}")
    logger.info(f"Query параметры: {dict(request.query_params)}")
    logger.info(f"Имя игрока: {player_name}")

    try:
        # Валидация имени игрока
        if not (2 <= len(player_name) <= 20):
            logger.warning(f"Некорректная длина имени: {len(player_name)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Имя игрока должно содержать от 2 до 20 символов"
            )

        # Генерация ID игрока
        player_id = str(uuid.uuid4())
        logger.info(f"Создан новый игрок. ID: {player_id}, Имя: {player_name}")
        
        response = ResponsePlayer(player_id=player_id)
        logger.info(f"Отправляем ответ: {response}")
        return response

    except HTTPException as e:
        logger.error(f"Ошибка валидации: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при авторизации: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )
