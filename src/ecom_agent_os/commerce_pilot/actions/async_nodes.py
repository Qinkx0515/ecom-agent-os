from decimal import Decimal
from uuid import uuid4

from ecom_agent_os.commerce_pilot.actions.async_dependencies import (
    AsyncActionDependencies,
)
from ecom_agent_os.commerce_pilot.actions.nodes import (
    ActionNodes,
)
from ecom_agent_os.commerce_pilot.actions.planner import (
    ActionPlanningError,
)
from ecom_agent_os.commerce_pilot.actions.repository import (
    ActionExecutionError,
)
from ecom_agent_os.commerce_pilot.actions.state import (
    ActionState,
)


class AsyncActionNodes(
    ActionNodes
):

    def __init__(
        self,
        deps: AsyncActionDependencies,
    ):

        self.deps = deps

    async def plan_action(
        self,
        state: ActionState,
    ) -> ActionState:

        try:

            plan = await (
                self.deps
                .action_planner(
                    state[
                        "user_request"
                    ]
                )
            )


        except ActionPlanningError as exc:

            return {
                "plan_ok":
                    False,

                "error":
                    str(exc),

                "status":
                    "planning_failed",
            }


        if not plan.is_supported:

            return {
                "plan_ok":
                    True,

                "is_supported":
                    False,

                "unsupported_reason":
                    plan
                    .unsupported_reason,

                "status":
                    "unsupported",
            }


        return {
            "action_id":
                state.get(
                    "action_id"
                )
                or str(
                    uuid4()
                ),

            "plan_ok":
                True,

            "is_supported":
                True,

            "action_type":
                plan.action_type,

            "sku":
                plan.sku,

            "new_price":
                str(
                    plan.new_price
                ),

            "rationale":
                plan.rationale,

            "status":
                "action_planned",
        }

    async def load_product(
        self,
        state: ActionState,
    ) -> ActionState:

        sku = state.get(
            "sku"
        )


        if not sku:

            return {
                "error":
                    "SKU is missing.",

                "status":
                    "product_load_failed",
            }


        product = await (
            self.deps
            .product_reader(
                sku
            )
        )


        if product is None:

            return {
                "error":
                    f"Product not found: "
                    f"{sku}",

                "status":
                    "product_load_failed",
            }


        return {
            "product_id":
                product.id,

            "product_name":
                product.name,

            "category":
                product.category,

            "old_price":
                str(
                    product.price
                ),

            "stock":
                product.stock,

            "status":
                "product_loaded",
        }

    async def execute_action(
        self,
        state: ActionState,
    ) -> ActionState:

        if (
            state.get(
                "approval_decision"
            )
            != "approve"
        ):

            return {
                "error":
                    "Action execution "
                    "requires approval.",

                "status":
                    "execution_blocked",
            }


        try:

            result = await (
                self.deps
                .price_updater(
                    sku=state[
                        "sku"
                    ],

                    new_price=Decimal(
                        state[
                            "new_price"
                        ]
                    ),

                    expected_old_price=(
                        Decimal(
                            state[
                                "old_price"
                            ]
                        )
                    ),
                )
            )


        except ActionExecutionError as exc:

            return {
                "error":
                    str(exc),

                "status":
                    "execution_failed",
            }


        return {
            "action_result": (
                f"商品 "
                f"{result.sku} "
                f"价格已由 "
                f"{result.old_price} "
                f"调整为 "
                f"{result.new_price}。"
            ),

            "status":
                "success",
        }