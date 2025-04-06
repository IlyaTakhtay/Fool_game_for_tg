from pydantic import BaseModel

class GameCreatedResponse(BaseModel):
    game_id: str
    players_limit: int

class GameJoinedResponse(BaseModel):
    game_id: str
    player_id: str
    player_name: str
    websocket_connection: str

class GameInfoResponse(BaseModel):
    game_id: str
    players_limit: int
    players_inside: int

class GameInfoListResponse(BaseModel):
    list: list[GameInfoResponse]
