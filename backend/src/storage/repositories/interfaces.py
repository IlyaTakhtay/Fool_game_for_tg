from abc import ABC, abstractmethod
from typing import List

from backend.src.game.models.game import FoolGame


class IGameRepository(ABC):
    """Абстрактный репозиторий для работы с играми"""

    @abstractmethod
    async def get_by_id(self, game_id: str) -> FoolGame | None:
        """Получить игру по ID"""
        pass

    @abstractmethod
    async def save(self, game: FoolGame) -> None:
        """Сохранить игру (автоматически индексирует по статусу)"""
        pass

    @abstractmethod
    async def delete(self, game_id: str) -> None:
        """Удалить игру"""
        pass

    @abstractmethod
    async def find_by_status(
        self, status: str, limit: int = 100, offset: int = 0
    ) -> List[FoolGame]:
        """
        Найти игры по статусу.
        status: 'pending', 'active', 'finished'
        """
        pass

    @abstractmethod
    async def find_by_player_id(self, player_id: str) -> FoolGame | None:
        """Найти игру игрока"""
        pass
