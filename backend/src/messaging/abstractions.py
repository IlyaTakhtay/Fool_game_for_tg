from abc import ABC, abstractmethod
from typing import Any, Dict, Callable

from pydantic import BaseModel


class AbstractEventBus(ABC):
    @abstractmethod
    async def publish(self, routing_key: str, event: BaseModel):
        pass
