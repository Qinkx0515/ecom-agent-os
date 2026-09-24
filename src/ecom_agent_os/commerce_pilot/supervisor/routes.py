from typing import Literal

from ecom_agent_os.commerce_pilot.supervisor.state import (
    SupervisorState,
)


def route_supervisor(
    state: SupervisorState,
) -> Literal[
    "analytics_agent",
    "action_agent",
    "unsupported",
    "failed",
]:

    if (
        state.get(
            "status"
        )
        == "routing_failed"
    ):

        return "failed"


    route = state.get(
        "route"
    )


    if route == "analytics":

        return "analytics_agent"


    if route == "action":

        return "action_agent"


    return "unsupported"