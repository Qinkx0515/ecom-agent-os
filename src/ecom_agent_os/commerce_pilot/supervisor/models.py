from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)


class SupervisorDecision(BaseModel):
    route: Literal[
        "analytics",
        "action",
        "unsupported",
    ]

    confidence: float = Field(
        ge=0,
        le=1,
    )

    reason: str
