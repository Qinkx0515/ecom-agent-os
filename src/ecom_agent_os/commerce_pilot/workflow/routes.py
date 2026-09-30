from typing import Literal

from ecom_agent_os.commerce_pilot.workflow.state import (
    CommerceGraphState,
)


def route_after_generation(
    state: CommerceGraphState,
) -> Literal[
    "execute_sql",
    "retry_or_fail",
    "unsupported",
]:

    if not state.get(
        "generation_ok",
        False,
    ):
        return "retry_or_fail"

    if not state.get(
        "is_supported",
        False,
    ):
        return "unsupported"

    return "execute_sql"


def route_after_execution(
    state: CommerceGraphState,
) -> Literal[
    "generate_answer",
    "retry_or_fail",
]:

    if state.get(
        "execution_ok",
        False,
    ):
        return "generate_answer"

    return "retry_or_fail"


def route_retry(
    state: CommerceGraphState,
) -> Literal[
    "generate_sql",
    "failed",
]:

    if state.get(
        "attempt_number",
        0,
    ) < state.get(
        "max_attempts",
        3,
    ):
        return "generate_sql"

    return "failed"
