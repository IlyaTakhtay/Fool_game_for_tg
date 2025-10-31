from pydantic import BaseModel


class PrivatePlayerData(BaseModel):
    status: str
    position: int
    cards: list[dict[str, str]]  # Для самого игрока
    allowed_actions: list[str] = []


class PublicPlayerData(BaseModel):
    player_id: str
    position: int
    cards_count: int  # Для других игроков
    status: str
    name: str  # Добавляем имя игрока


class PublicGameData(BaseModel):
    room_size: int
    room_players: list[PublicPlayerData]
    deck_size: int
    trump_suit: str | None = None
    trump_rank: str | None = None
    attacker_position: int | None = None
    defender_position: int | None = None
    table_cards: list[dict] = []


class FullGameStateToPlayer(PrivatePlayerData, PublicGameData):
    """Модель данных с полным состоянием игры для игрока"""

    current_state: str | None = None
    pass


class PlayerStatusData(BaseModel):
    player_id: str
    status: str


class SelfStatusUpdateData(BaseModel):
    status: str
    allowed_actions: list[str]


class GameOverData(BaseModel):
    winner_id: str | None
    loser_ids: list[str]
