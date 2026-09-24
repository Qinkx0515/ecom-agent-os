from dataclasses import dataclass
from typing import Callable

from ecom_agent_os.commerce_pilot.actions.models import (
    ActionPlan,
)
from ecom_agent_os.commerce_pilot.actions.planner import (
    generate_action_plan,
)
from ecom_agent_os.commerce_pilot.actions.repository import (
    PriceUpdateResult,
    ProductSnapshot,
    get_product_snapshot,
    update_product_price,
)


@dataclass(
    frozen=True,
)
class ActionDependencies:

    action_planner: Callable[
        [str],
        ActionPlan,
    ] = generate_action_plan


    product_reader: Callable[
        [str],
        ProductSnapshot | None,
    ] = get_product_snapshot


    price_updater: Callable[
        ...,
        PriceUpdateResult,
    ] = update_product_price