import operator
from typing import (
    Annotated,
    Any,
    Literal,
    TypedDict,
)


class AttemptTrace(TypedDict):
    attempt: int

    stage: Literal[
        "generation",
        "execution",
    ]

    sql: str | None

    status: Literal[
        "success",
        "failed",
    ]

    error: str | None


class CommerceGraphState(
    TypedDict,
    total=False,
):
    # ===== User Input =====

    question: str

    # ===== Context =====

    schema: str

    max_attempts: int

    # ===== Current Attempt =====

    attempt_number: int

    query_plan: list[str]

    current_sql: str | None

    # ===== Generation =====

    generation_ok: bool

    is_supported: bool

    unsupported_reason: str | None

    # ===== Execution =====

    execution_ok: bool

    columns: list[str]

    rows: list[dict[str, Any]]

    truncated: bool

    # ===== Error =====

    last_error: str | None

    # ===== Final =====

    final_answer: str

    status: str

    # ===== Trace =====

    attempts: Annotated[
        list[AttemptTrace],
        operator.add,
    ]
