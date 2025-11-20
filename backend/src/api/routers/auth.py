import logging
import uuid
from fastapi import APIRouter, HTTPException, Request, status, Response

from backend.src.api.models.game import PlayerAuthResponse
from backend.src.settings import AppSettings, JWTSettings
from backend.src.api.dependencies.jwt_auth import create_access_token
from backend.src.game.utils.name_generator import generate_player_name_with_suffix

app_settings = AppSettings()
jwt_settings = JWTSettings()
logger = logging.getLogger(__name__)
router = APIRouter(prefix=f"/api/{app_settings.api_version_prefix}", tags=["Auth"])


@router.post("/auth_guest", response_model=PlayerAuthResponse)
async def auth_guest(request: Request, response: Response) -> PlayerAuthResponse:
    """Аутентификация гостевого игрока.

    Генерирует случайное имя и уникальный ID игрока,
    возвращая JWT токен в httpOnly куки.

    Args:
        request: Объект запроса.
        response: Объект ответа для установки куки.

    Returns:
        Объект Response с JWT токеном в httpOnly куки.

    Raises:
        HTTPException: При возникновении непредвиденных ошибок.
    """
    logger.info(
        f"Получен запрос на авторизацию гостя. Headers: {dict(request.headers)}"
    )

    try:
        player_name = generate_player_name_with_suffix()
        player_id = str(uuid.uuid4())
        logger.info(f"Создан новый игрок. ID: {player_id}, Имя: {player_name}")

        access_token_data = {"player_id": player_id, "player_name": player_name}
        access_token = create_access_token(access_token_data)

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="lax",
            secure=jwt_settings.cookie_secure,
            max_age=jwt_settings.access_token_expire_hours * 3600,
        )
        return PlayerAuthResponse(**access_token_data)

    except Exception as e:
        logger.error(f"Неожиданная ошибка при авторизации: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера",
        )


@router.post("/logout")
async def logout(response: Response):
    """Удаление аутентификационной cookie."""
    response.set_cookie(
        key="access_token",
        value="",
        httponly=True,
        samesite="lax",
        secure=jwt_settings.cookie_secure,
        max_age=0,  # Установка max_age=0 удаляет cookie
    )
    response.status_code = status.HTTP_200_OK
    return {"status": "ok", "detail": "Logged out"}
