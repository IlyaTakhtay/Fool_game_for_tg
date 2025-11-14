from abc import ABC, abstractmethod
from typing import Any, Dict, Callable

from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class BaseEvent(BaseModel):
    id: UUID = Field(default_factory=uuid4)


class AbstractEventBus(ABC):
    @abstractmethod
    async def publish(self, routing_key: str, event: BaseEvent):
        pass
