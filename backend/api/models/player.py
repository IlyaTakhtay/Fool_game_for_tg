from pydantic import BaseModel

# Модель ответа для клиента
class ResponsePlayer(BaseModel):
    """Модель ответа для игрока"""
    player_id: str
