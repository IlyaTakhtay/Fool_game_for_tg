import logging
import uuid

from fastapi import APIRouter, HTTPException, Request, status

from backend.api.models.player import ResponsePlayer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Auth"])


@router.post("/auth_guest", response_model=ResponsePlayer)
async def auth_guest(request: Request, player_name: str) -> ResponsePlayer:
    """Аутентификация гостевого игрока.

    Генерирует уникальный ID игрока и возвращает его.

    Args:
        request: Объект запроса.
        player_name: Имя игрока.

    Returns:
        Объект ResponsePlayer, содержащий player_id.

    Raises:
        HTTPException: Если имя игрока не содержит от 2 до 20 символов.
        HTTPException: При возникновении других непредвиденных ошибок.
    """
    logger.info(
        f"Получен запрос на авторизацию гостя. Headers: {dict(request.headers)}"
    )
    logger.info(f"Query параметры: {dict(request.query_params)}")
    logger.info(f"Имя игрока: {player_name}")

    try:
        if not (2 <= len(player_name) <= 20):
            logger.warning(f"Некорректная длина имени: {len(player_name)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Имя игрока должно содержать от 2 до 20 символов",
            )

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
            detail="Внутренняя ошибка сервера",
        )
