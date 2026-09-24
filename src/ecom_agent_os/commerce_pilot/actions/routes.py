from typing import Literal

from ecom_agent_os.commerce_pilot.actions.state import (
    ActionState,
)


def route_after_plan(
    state: ActionState,
) -> Literal[
    "load_product",
    "unsupported",
    "failed",
]:

    if not state.get(
        "plan_ok",
        False,
    ):

        return "failed"

    if not state.get(
        "is_supported",
        False,
    ):

        return "unsupported"

    return "load_product"


def route_after_product(
    state: ActionState,
) -> Literal[
    "assess_risk",
    "failed",
]:

    if (
        state.get(
            "status"
        )
        != "product_loaded"
    ):

        return "failed"

    return "assess_risk"


def route_after_risk(
    state: ActionState,
) -> Literal[
    "human_approval",
    "failed",
]:

    if (
        state.get(
            "status"
        )
        != "risk_assessed"
    ):

        return "failed"

    return "human_approval"


def route_after_approval(
    state: ActionState,
) -> Literal[
    "execute_action",
    "rejected",
]:

    if (
        state.get(
            "approval_decision"
        )
        == "approve"
    ):

        return "execute_action"

    return "rejected"