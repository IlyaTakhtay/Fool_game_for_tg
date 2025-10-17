from pydantic import BaseModel


class GameCreatedResponse(BaseModel):
    game_id: str


class GameJoinedResponse(BaseModel):
    game_id: str
    player_id: str
    websocket_connection: str


class GameInfoResponse(BaseModel):
    game_id: str
    players_limit: int
    players_inside: int
    websocket_connection: str | None = None


class GameInfoListResponse(BaseModel):
    list: list[GameInfoResponse]
