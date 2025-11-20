from typing import Annotated

from dishka import FromComponent, Provider, Scope, provide
from redis.asyncio import Redis

from backend.src.api.managers.game_manager import GameManager
from backend.src.messaging.abstractions import AbstractEventBus
from backend.src.storage.repositories.interfaces import IGameRepository
from backend.src.di.components import Components


class GameProvider(Provider):
    """Предоставляет сервис для управления игровой логикой."""

    @provide(scope=Scope.APP)
    def get_game_service(
        self,
        game_repository: Annotated[IGameRepository, FromComponent(Components.GAME)],
        event_bus: AbstractEventBus,
        redis: Annotated[Redis, FromComponent("")],
    ) -> GameManager:
        return GameManager(game_repository, event_bus, redis)
