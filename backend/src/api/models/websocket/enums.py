from enum import Enum


class IncomingMessageType(str, Enum):
    """Сообщения, отправляемые клиентом на сервер."""

    PLAYER_CONNECTED = "player_connected"
    CHANGE_STATUS = "change_status"
    PLAY_CARD = "play_card"
    PASS_TURN = "pass_turn"
    QUIT_GAME = "quit_game"


class OutgoingMessageType(str, Enum):
    """Сообщения, отправляемые сервером клиенту."""

    # Connection
    CONNECTION_CONFIRMED = "connection_confirmed"
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"
    PLAYER_DISCONNECTED = "player_disconnected"

    # Status & State Updates
    GAME_STATE_UPDATE = "game_state_update"
    PLAYER_STATUS_CHANGED = "player_status_changed"

    # Game Events
    GAME_STARTED = "game_started"
    ROUND_ENDED = "round_ended"
    GAME_ENDED = "game_ended"

    # Errors
    ERROR = "error"
