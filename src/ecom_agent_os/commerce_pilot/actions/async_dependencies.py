from dataclasses import dataclass
from typing import (
    Awaitable,
    Callable,
)

from ecom_agent_os.commerce_pilot.actions.async_planner import (
    async_generate_action_plan,
)
from ecom_agent_os.commerce_pilot.actions.async_repository import (
    async_get_product_snapshot,
    async_update_product_price,
)
from ecom_agent_os.commerce_pilot.actions.models import (
    ActionPlan,
)
from ecom_agent_os.commerce_pilot.actions.repository import (
    PriceUpdateResult,
    ProductSnapshot,
)


@dataclass(
    frozen=True,
)
class AsyncActionDependencies:

    action_planner: Callable[
        [str],
        Awaitable[
            ActionPlan
        ],
    ] = (
        async_generate_action_plan
    )


    product_reader: Callable[
        [str],
        Awaitable[
            ProductSnapshot
            | None
        ],
    ] = (
        async_get_product_snapshot
    )


    price_updater: Callable[
        ...,
        Awaitable[
            PriceUpdateResult
        ],
    ] = (
        async_update_product_price
    )