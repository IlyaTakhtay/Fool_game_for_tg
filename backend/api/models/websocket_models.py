from pydantic import BaseModel
from typing import Optional, Any, Dict
from enum import Enum


class MessageType(str, Enum):
    # Connection
    PLAYER_CONNECTED = "player_connected"
    PLAYER_DISCONNECTED = "player_disconnected"
    PLAYER_STATUS = "player_status"

    # Game Actions
    PLAY_CARD = "play_card"
    COLLECT_CARDS = "collect_cards"
    PASS_TURN = "pass_turn"

    # Game Events (outgoing)
    CONNECTION_CONFIRMED = "connection_confirmed"
    GAME_STATE_UPDATE = "game_state_update"
    CARD_PLAYED = "card_played"
    ROUND_ENDED = "round_ended"
    GAME_STARTED = "game_started"
    GAME_ENDED = "game_ended"
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"

    # Errors
    ERROR = "error"


# === INCOMING MESSAGES (от клиента) ===


class PlayCardRequest(BaseModel):
    """Сыграть карту"""

    type: MessageType = MessageType.PLAY_CARD
    card: dict[str, str]  # {"rank": "ace", "suit": "spades"}


# class CollectCardsRequest(BaseModel):
#     """Собрать карты со стола"""
#     type: MessageType = MessageType.COLLECT_CARDS

# class PassTurnRequest(BaseModel):
#     """Пропустить ход"""
#     type: MessageType = MessageType.PASS_TURN

# === OUTGOING MESSAGES (к клиенту) ===


class PrivatePlayerData(BaseModel):
    status: str
    position: int
    cards: list[dict[str, str]]  # Для самого игрока


class PlayerConnectionResponse(BaseModel):
    type: MessageType = MessageType.CONNECTION_CONFIRMED
    data: PrivatePlayerData


class PublicPlayerData(BaseModel):
    player_id: str
    position: int
    cards_count: int  # Для других игроков
    status: str
    name: str  # Добавляем имя игрока


class PlayerJoinedResponse(BaseModel):
    type: MessageType = MessageType.PLAYER_JOINED
    data: PublicPlayerData


class PublicGameData(BaseModel):
    room_size: int
    room_players: list[PublicPlayerData]
    deck_size: int
    trump_suit: str
    trump_rank: str
    attacker_position: int
    defender_position: int | None = None
    table_cards: list[dict] = []


class ReconnectionData(PrivatePlayerData, PublicGameData):
    pass


class ReconnectionResponse(BaseModel):
    type: MessageType = MessageType.CONNECTION_CONFIRMED
    data: ReconnectionData


class PlayerDisconnectedData(BaseModel):
    player_id: str


class PlayerDisconnectedResponse(BaseModel):
    type: MessageType = MessageType.PLAYER_DISCONNECTED
    data: PlayerDisconnectedData


class PlayerStatusData(BaseModel):
    player_id: str
    status: str


class PlayerStatusChangedResponse(BaseModel):
    type: MessageType = MessageType.PLAYER_STATUS
    data: PlayerStatusData


class GameStateUpdateResponse(BaseModel):
    """Обновление состояния игры"""

    type: MessageType = MessageType.GAME_STATE_UPDATE
    data: Dict[str, Any]  # полное состояние игры


class CardPlayedResponse(BaseModel):
    """Карта была сыграна"""

    type: MessageType = MessageType.CARD_PLAYED
    data: Dict[str, Any] = {
        "player_position": 1,  # позиция игрока (не ID!)
        "card": {"rank": "ace", "suit": "spades"},
        "is_attack": True,
    }


class PlayerJoinedResponse(BaseModel):
    """Новый игрок присоединился"""

    type: MessageType = MessageType.PLAYER_JOINED
    data: PublicPlayerData


class PlayerLeftResponse(BaseModel):
    """Игрок покинул игру"""

    type: MessageType = MessageType.PLAYER_LEFT
    data: Dict[str, Any] = {
        "player_position": 2,
        "players_count": 2,
    }


class RoundEndedResponse(BaseModel):
    """Раунд завершен"""

    type: MessageType = MessageType.ROUND_ENDED
    data: Dict[str, Any] = {
        "winner_position": 1,
        "collected_cards": [{"rank": "ace", "suit": "spades"}],
    }


class GameStartedResponse(BaseModel):
    """Игра началась"""

    type: MessageType = MessageType.GAME_STARTED
    data: Dict[str, Any] = {
        "trump_suit": "hearts",
        "your_cards": [{"rank": "ace", "suit": "spades"}],
        "first_player_position": 1,
    }


class ErrorResponse(BaseModel):
    """Ошибка"""

    type: MessageType = MessageType.ERROR
    data: Dict[str, str] = {
        "message": "Invalid action",
        "code": "INVALID_CARD",
    }
