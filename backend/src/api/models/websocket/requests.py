from pydantic import BaseModel, Field
from typing import Literal, Union

from backend.src.api.models.game import Card
from .enums import IncomingMessageType


# --- Data Models for Requests ---


class ChangeStatusData(BaseModel):
    status: str


class PlayCardData(BaseModel):
    attack_card: Card
    defend_card: Card | None = None


# --- Base Request Model ---


class BaseRequest(BaseModel):
    type: IncomingMessageType


# --- Specific Request Models ---


class PlayerConnectedRequest(BaseRequest):
    type: Literal[IncomingMessageType.PLAYER_CONNECTED]


class ChangeStatusRequest(BaseRequest):
    type: Literal[IncomingMessageType.CHANGE_STATUS]
    data: ChangeStatusData


class PlayCardRequest(BaseRequest):
    type: Literal[IncomingMessageType.PLAY_CARD]
    data: PlayCardData


class PassTurnRequest(BaseRequest):
    type: Literal[IncomingMessageType.PASS_TURN]


class QuitGameRequest(BaseRequest):
    type: Literal[IncomingMessageType.QUIT_GAME]


# --- Union of all possible incoming messages ---

IncomingMessage = Union[
    PlayerConnectedRequest,
    ChangeStatusRequest,
    PlayCardRequest,
    PassTurnRequest,
    QuitGameRequest,
]
