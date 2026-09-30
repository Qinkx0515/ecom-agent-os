from dataclasses import dataclass
from typing import (
    Awaitable,
    Callable,
)

from ecom_agent_os.commerce_pilot.actions.async_dependencies import (
    AsyncActionDependencies,
)
from ecom_agent_os.commerce_pilot.supervisor.async_router import (
    async_route_request,
)
from ecom_agent_os.commerce_pilot.supervisor.models import (
    SupervisorDecision,
)
from ecom_agent_os.commerce_pilot.workflow.async_dependencies import (
    AsyncCommerceDependencies,
)


@dataclass(
    frozen=True,
)
class AsyncSupervisorDependencies:
    request_router: Callable[
        [str],
        Awaitable[SupervisorDecision],
    ] = async_route_request

    analytics_deps: AsyncCommerceDependencies | None = None

    action_deps: AsyncActionDependencies | None = None
