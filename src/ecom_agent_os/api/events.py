from dataclasses import dataclass
from typing import Any

from fastapi.encoders import (
    jsonable_encoder,
)
from fastapi.sse import (
    ServerSentEvent,
)


@dataclass
class AgentEvent:
    event: str

    data: dict[str, Any]

    event_id: str | None = None

    def to_sse(
        self,
    ) -> ServerSentEvent:

        return ServerSentEvent(
            event=self.event,
            id=self.event_id,
            data=jsonable_encoder(self.data),
        )
