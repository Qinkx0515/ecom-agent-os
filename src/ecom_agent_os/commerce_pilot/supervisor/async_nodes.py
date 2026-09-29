from ecom_agent_os.commerce_pilot.actions.async_builder import (
    build_async_action_graph,
)
from ecom_agent_os.commerce_pilot.supervisor.async_dependencies import (
    AsyncSupervisorDependencies,
)
from ecom_agent_os.commerce_pilot.supervisor.nodes import (
    SupervisorNodes,
)
from ecom_agent_os.commerce_pilot.supervisor.router import (
    SupervisorRoutingError,
)
from ecom_agent_os.commerce_pilot.supervisor.state import (
    SupervisorState,
)
from ecom_agent_os.commerce_pilot.workflow.async_builder import (
    build_async_commerce_graph,
)


class AsyncSupervisorNodes(
    SupervisorNodes
):

    def __init__(
        self,
        deps: AsyncSupervisorDependencies,
    ):

        self.deps = deps


        self.analytics_graph = (
            build_async_commerce_graph(
                deps=(
                    deps.analytics_deps
                )
            )
        )


        self.action_graph = (
            build_async_action_graph(
                deps=(
                    deps.action_deps
                )
            )
        )

    async def supervisor(
        self,
        state: SupervisorState,
    ) -> SupervisorState:

        try:

            decision = await (
                self.deps
                .request_router(
                    state[
                        "request"
                    ]
                )
            )


        except SupervisorRoutingError as exc:

            return {
                "status":
                    "routing_failed",

                "error":
                    str(exc),
            }


        return {
            "route":
                decision.route,

            "route_confidence":
                decision.confidence,

            "route_reason":
                decision.reason,

            "status":
                "routed",
        }

    async def analytics_agent(
        self,
        state: SupervisorState,
    ) -> SupervisorState:

        result = await (
            self.analytics_graph
            .ainvoke(
                {
                    "question":
                        state[
                            "request"
                        ],

                    "max_attempts":
                        3,

                    "attempts":
                        [],
                }
            )
        )


        return {
            "agent_used":
                "analytics",

            "child_status":
                result.get(
                    "status",
                    "unknown",
                ),

            "child_data": {
                "sql":
                    result.get(
                        "current_sql"
                    ),

                "query_plan":
                    result.get(
                        "query_plan",
                        [],
                    ),

                "attempts":
                    result.get(
                        "attempts",
                        [],
                    ),
            },

            "final_answer":
                result.get(
                    "final_answer",
                    "分析未返回结果。",
                ),

            "status":
                (
                    "success"

                    if result.get(
                        "status"
                    )
                    in {
                        "success",
                        "partial_success",
                    }

                    else "child_failed"
                ),
        }

    async def action_agent(
        self,
        state: SupervisorState,
    ) -> SupervisorState:

        result = await (
            self.action_graph
            .ainvoke(
                {
                    "user_request":
                        state[
                            "request"
                        ]
                }
            )
        )


        return {
            "agent_used":
                "action",

            "child_status":
                result.get(
                    "status",
                    "unknown",
                ),

            "child_data": {
                "action_id":
                    result.get(
                        "action_id"
                    ),

                "action_type":
                    result.get(
                        "action_type"
                    ),

                "sku":
                    result.get(
                        "sku"
                    ),

                "risk_level":
                    result.get(
                        "risk_level"
                    ),

                "approval_decision":
                    result.get(
                        "approval_decision"
                    ),
            },

            "final_answer":
                (
                    result.get(
                        "action_result"
                    )
                    or
                    "业务操作已结束。"
                ),

            "status":
                (
                    "success"

                    if result.get(
                        "status"
                    )
                    in {
                        "success",
                        "rejected",
                    }

                    else "child_failed"
                ),
        }