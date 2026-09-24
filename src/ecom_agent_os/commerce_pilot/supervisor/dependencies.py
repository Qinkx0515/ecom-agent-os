from dataclasses import dataclass
from typing import Callable

from ecom_agent_os.commerce_pilot.actions.dependencies import (
    ActionDependencies,
)
from ecom_agent_os.commerce_pilot.supervisor.models import (
    SupervisorDecision,
)
from ecom_agent_os.commerce_pilot.supervisor.router import (
    route_request,
)
from ecom_agent_os.commerce_pilot.workflow.dependencies import (
    CommerceDependencies,
)


@dataclass(
    frozen=True,
)
class SupervisorDependencies:

    request_router: Callable[
        [str],
        SupervisorDecision,
    ] = route_request


    analytics_deps: (
        CommerceDependencies
        | None
    ) = None


    action_deps: (
        ActionDependencies
        | None
    ) = None