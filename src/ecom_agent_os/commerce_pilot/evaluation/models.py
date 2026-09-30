from typing import Literal

from pydantic import BaseModel, Field


class RoutingEvalCase(BaseModel):
    id: str

    question: str

    expected_route: Literal[
        "analytics",
        "action",
        "unsupported",
    ]

    difficulty: str


class AnalyticsEvalCase(BaseModel):
    id: str

    question: str

    difficulty: str

    tags: list[str] = Field(default_factory=list)

    expected_sql: str


class RoutingEvalResult(BaseModel):
    id: str

    question: str

    expected_route: str

    predicted_route: str | None

    correct: bool

    latency_ms: float

    error: str | None = None


class AnalyticsEvalResult(BaseModel):
    id: str

    question: str

    difficulty: str

    tags: list[str]

    generated_sql: str | None

    execution_success: bool

    result_correct: bool

    task_success: bool

    attempts: int

    latency_ms: float

    error: str | None = None
