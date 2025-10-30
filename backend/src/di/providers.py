from dishka import AsyncContainer, Provider, make_async_container, provide, Scope
from redis.asyncio import Redis
from collections.abc import AsyncIterator
from backend.src.api.managers.connection_managaer import ConnectionManager
from backend.src.api.managers.game_manager import GameManager
from backend.src.config import RedisSettings, StorageSettings
from backend.src.storage.repositories.interfaces import IGameRepository
from backend.src.storage.repositories.redis import RedisGameRepository


class StorageProvider(Provider): #TODO: make it real strorage provider by different databases not only cover on redis
    @provide(scope=Scope.APP)
    def get_storage_settings(
        self,
    ) -> StorageSettings:
        settings: StorageSettings = RedisSettings()
        return settings

    @provide(scope=Scope.APP)
    async def get_storage_client(
        self,
        redis_settings: StorageSettings,
    ) -> AsyncIterator[Redis]:
        client = Redis.from_url(
            redis_settings.redis_url,
            password=redis_settings.redis_password,
            decode_responses=redis_settings.redis_decode_responses,
        )
        yield client
        await client.aclose()


class GameProvider(Provider):
    """Зависимости для игрового домена"""

    @provide(scope=Scope.APP)
    def get_game_repository(
        self,
        redis: Redis,
    ) -> IGameRepository:
        """Репозиторий игр"""
        return RedisGameRepository(client=redis)

    @provide(scope=Scope.APP)
    def get_game_service(
        self,
        game_repository: IGameRepository,
    ) -> GameManager:
        """Сервис с бизнес-логикой игр"""
        return GameManager(game_repository)


class WebSocketProvider(Provider):
    """Зависимости для WebSocket"""

    @provide(scope=Scope.APP)
    def get_connection_manager(
        self,
    ) -> ConnectionManager:
        """Менеджер WebSocket соединений (синглтон)"""
        return ConnectionManager()


def create_container() -> AsyncContainer:
    return make_async_container(
        StorageProvider(),
        GameProvider(),
        WebSocketProvider(),
    )
