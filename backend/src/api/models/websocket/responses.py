from pydantic import BaseModel
from typing import Any, Dict

from .enums import OutgoingMessageType
from .data import (
    PrivatePlayerData,
    PublicPlayerData,
    FullGameStateToPlayer,
    GameOverData,
)


class PlayerConnectionResponse(BaseModel):
    type: OutgoingMessageType = OutgoingMessageType.CONNECTION_CONFIRMED
    data: PrivatePlayerData


class PlayerJoinedResponse(BaseModel):
    """Новый игрок присоединился"""

    type: OutgoingMessageType = OutgoingMessageType.PLAYER_JOINED
    data: PublicPlayerData


class PlayerGameStateResponse(BaseModel):
    type: OutgoingMessageType = OutgoingMessageType.CONNECTION_CONFIRMED
    data: FullGameStateToPlayer


class GameStateUpdateResponse(BaseModel):
    """Обновление состояния игры"""

    type: OutgoingMessageType = OutgoingMessageType.GAME_STATE_UPDATE
    data: Dict[str, Any]  # полное состояние игры


class ErrorResponse(BaseModel):
    """Ошибка"""

    type: OutgoingMessageType = OutgoingMessageType.ERROR
    data: Dict[str, str] = {
        "message": "Invalid action",
        "code": "INVALID_CARD",
    }


class GameOverResponse(BaseModel):
    type: OutgoingMessageType = OutgoingMessageType.GAME_ENDED
    data: GameOverData
