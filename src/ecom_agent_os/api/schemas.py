from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)


class ChatRequest(BaseModel):
    request: str = Field(
        min_length=1,
        max_length=2000,
    )


class ApprovalRequest(BaseModel):
    thread_id: str = Field(
        min_length=1,
        max_length=200,
    )

    decision: Literal[
        "approve",
        "reject",
    ]

    comment: str | None = Field(
        default=None,
        max_length=500,
    )


class HealthResponse(BaseModel):
    status: str

    service: str

    version: str


class ThreadResponse(BaseModel):
    thread_id: str

    status: str | None

    route: str | None

    agent_used: str | None

    final_answer: str | None

    next_nodes: list[str]
