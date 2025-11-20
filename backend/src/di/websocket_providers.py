from dishka import Provider, Scope, provide

from backend.src.api.managers.connection_managaer import (
    DistributedConnectionManager,
)
from backend.src.messaging.abstractions import AbstractEventBus


class WebSocketProvider(Provider):
    """Предоставляет зависимости, связанные с WebSocket."""

    @provide(scope=Scope.APP)
    def get_connection_manager(
        self,
        event_bus: AbstractEventBus,
    ) -> DistributedConnectionManager:
        """Предоставляет синглтон `DistributedConnectionManager` для WebSocket-соединений."""

        return DistributedConnectionManager(event_bus)
