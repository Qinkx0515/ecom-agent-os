from typing import (
    Any,
    Literal,
    TypedDict,
)


class SupervisorState(
    TypedDict,
    total=False,
):
    # ===== Input =====

    request: str

    # ===== Routing =====

    route: Literal[
        "analytics",
        "action",
        "unsupported",
    ]

    route_confidence: float

    route_reason: str

    agent_used: str

    # ===== Child Agent Result =====

    child_status: str

    child_data: dict[str, Any]

    # ===== Output =====

    final_answer: str

    status: str

    error: str | None
