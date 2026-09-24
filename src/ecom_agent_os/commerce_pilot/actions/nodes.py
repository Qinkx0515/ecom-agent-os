from decimal import Decimal
from uuid import uuid4

from pydantic import ValidationError

from langgraph.types import (
    interrupt,
)

from ecom_agent_os.commerce_pilot.actions.dependencies import (
    ActionDependencies,
)
from ecom_agent_os.commerce_pilot.actions.models import (
    ApprovalDecision,
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


class ActionNodes:

    def __init__(
        self,
        deps: ActionDependencies,
    ):

        self.deps = deps


    def plan_action(
        self,
        state: ActionState,
    ) -> ActionState:

        try:

            plan = (
                self.deps
                .action_planner(
                    state[
                        "user_request"
                    ]
                )
            )

        except ActionPlanningError as exc:

            return {
                "plan_ok": False,
                "error": str(exc),
                "status":
                    "planning_failed",
            }


        if not plan.is_supported:

            return {
                "plan_ok": True,
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

    def load_product(
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


        product = (
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


    def assess_risk(
        self,
        state: ActionState,
    ) -> ActionState:

        old_price = Decimal(
            state[
                "old_price"
            ]
        )

        new_price = Decimal(
            state[
                "new_price"
            ]
        )


        if old_price <= 0:

            return {
                "error":
                    "Invalid old price.",
                "status":
                    "risk_assessment_failed",
            }


        change_pct = (
            (
                new_price
                - old_price
            )
            /
            old_price
            * Decimal("100")
        )


        absolute_change = abs(
            change_pct
        )


        if (
            absolute_change
            >= Decimal("30")
        ):

            risk_level = "high"

        elif (
            absolute_change
            >= Decimal("10")
        ):

            risk_level = "medium"

        else:

            risk_level = "low"


        return {
            "price_change_pct":
                round(
                    float(
                        change_pct
                    ),
                    2,
                ),

            "risk_level":
                risk_level,

            # V5 中任何数据库写操作
            # 都必须审批
            "approval_required":
                True,

            "status":
                "risk_assessed",
        }

    def human_approval(
        self,
        state: ActionState,
    ) -> ActionState:

        payload = {
            "type":
                "business_action_approval",

            "action_id":
                state[
                    "action_id"
                ],

            "action_type":
                state[
                    "action_type"
                ],

            "sku":
                state[
                    "sku"
                ],

            "product_name":
                state[
                    "product_name"
                ],

            "category":
                state[
                    "category"
                ],

            "old_price":
                state[
                    "old_price"
                ],

            "new_price":
                state[
                    "new_price"
                ],

            "price_change_pct":
                state[
                    "price_change_pct"
                ],

            "risk_level":
                state[
                    "risk_level"
                ],

            "message": (
                "该操作将修改数据库中的"
                "商品价格，请人工确认。"
            ),
        }


        while True:

            response = interrupt(
                payload
            )


            try:

                decision = (
                    ApprovalDecision
                    .model_validate(
                        response
                    )
                )

            except ValidationError:

                payload = {
                    **payload,

                    "validation_error":
                        (
                            "审批结果必须包含 "
                            "decision=approve "
                            "或 decision=reject"
                        ),
                }

                continue


            return {
                "approval_decision":
                    decision.decision,

                "approval_comment":
                    decision.comment,

                "status":
                    (
                        "approved"
                        if (
                            decision.decision
                            == "approve"
                        )
                        else "rejected"
                    ),
            }



    def execute_action(
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
                    (
                        "Action execution "
                        "requires approval."
                    ),

                "status":
                    "execution_blocked",
            }


        try:

            result = (
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


    def rejected(
        self,
        state: ActionState,
    ) -> ActionState:

        return {
            "action_result":
                (
                    "操作已被人工拒绝，"
                    "数据库未进行修改。"
                ),

            "status":
                "rejected",
        }


    def unsupported(
        self,
        state: ActionState,
    ) -> ActionState:

        return {
            "action_result":
                (
                    "该业务操作暂不支持："
                    f"{state.get('unsupported_reason')}"
                ),

            "status":
                "unsupported",
        }


    def failed(
        self,
        state: ActionState,
    ) -> ActionState:

        return {
            "action_result":
                (
                    "业务操作执行失败："
                    f"{state.get('error')}"
                ),

            "status":
                "failed",
        }