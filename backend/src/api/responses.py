from typing import Any
import msgspec.json
from fastapi.responses import Response
from pydantic import BaseModel


class MsgSpecJSONResponse(Response):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        if isinstance(content, BaseModel):
            content = content.model_dump()
        return msgspec.json.encode(content)
