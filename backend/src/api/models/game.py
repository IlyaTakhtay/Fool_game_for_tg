from pydantic import BaseModel
from typing import List, Optional


class Card(BaseModel):
    rank: str
    suit: str


class Player(BaseModel):
    player_id: str
    position: int
    cards_count: int
    status: str
    name: str


class TablePair(BaseModel):
    attack_card: Card
    defend_card: Optional[Card] = None


class GameState(BaseModel):
    current_state: str
    room_size: int
    room_players: List[Player]
    deck_size: int
    trump_suit: Optional[str] = None
    trump_rank: Optional[str] = None
    attacker_position: int
    defender_position: Optional[int] = None
    table: List[TablePair] = []


class GameCreatedResponse(BaseModel):
    game_id: str


class GameJoinedResponse(BaseModel):
    game_id: str
    player_id: str
    websocket_connection: str
    game_state: GameState


class GameInfoResponse(BaseModel):
    game_id: str
    players_limit: int
    players_inside: int
    websocket_connection: str | None = None
