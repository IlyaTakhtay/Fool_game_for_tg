from dishka import make_async_container, AsyncContainer
from .storage_providers import RedisClientProvider, RedisGameRepositoryProvider
from .messaging_providers import RabbitMQProvider
from .game_providers import GameProvider
from .websocket_providers import WebSocketProvider


def create_container() -> AsyncContainer:
    """Создает и конфигурирует контейнер внедрения зависимостей Dishka."""
    return make_async_container(
        RedisClientProvider(),
        RedisGameRepositoryProvider(),
        RabbitMQProvider(),
        GameProvider(),
        WebSocketProvider(),
    )
