from typing import List, Dict, Any

from backend.src.messaging.abstractions import BaseEvent


class PlayerJoinedEvent(BaseEvent):
    player_id: str
    game_id: str


class GameStateChangedEvent(BaseEvent):
    game_id: str


class GameOverEvent(BaseEvent):
    game_id: str
    winner_id: str
    loser_ids: List[str]
