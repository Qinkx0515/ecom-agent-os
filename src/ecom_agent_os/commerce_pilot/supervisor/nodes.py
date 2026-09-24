from ecom_agent_os.commerce_pilot.actions.builder import (
    build_action_graph,
)
from ecom_agent_os.commerce_pilot.supervisor.dependencies import (
    SupervisorDependencies,
)
from ecom_agent_os.commerce_pilot.supervisor.router import (
    SupervisorRoutingError,
)
from ecom_agent_os.commerce_pilot.supervisor.state import (
    SupervisorState,
)
from ecom_agent_os.commerce_pilot.workflow.builder import (
    build_commerce_graph,
)


class SupervisorNodes:

    def __init__(
        self,
        deps: SupervisorDependencies,
    ):

        self.deps = deps


        # 子图这里不单独传父级 checkpointer。
        #
        # 默认 compile() 模式可以在嵌套 Graph 中
        # 继承父图的 checkpoint 上下文，
        # 并支持 interrupt / resume。

        self.analytics_graph = (
            build_commerce_graph(
                deps=deps.analytics_deps
            )
        )

        self.action_graph = (
            build_action_graph(
                deps=deps.action_deps
            )
        )



    def supervisor(
        self,
        state: SupervisorState,
    ) -> SupervisorState:

        try:

            decision = (
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


    def analytics_agent(
        self,
        state: SupervisorState,
    ) -> SupervisorState:

        result = (
            self.analytics_graph.invoke(
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

                "rows":
                    result.get(
                        "rows",
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


    def action_agent(
        self,
        state: SupervisorState,
    ) -> SupervisorState:

        result = (
            self.action_graph.invoke(
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

                "old_price":
                    result.get(
                        "old_price"
                    ),

                "new_price":
                    result.get(
                        "new_price"
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
                    or "业务操作已结束。"
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


    def unsupported(
        self,
        state: SupervisorState,
    ) -> SupervisorState:

        return {
            "agent_used":
                "none",

            "final_answer":
                (
                    "当前 CommercePilot "
                    "暂时只支持经营数据分析"
                    "以及单商品价格调整。"
                ),

            "status":
                "unsupported",
        }


    def failed(
        self,
        state: SupervisorState,
    ) -> SupervisorState:

        return {
            "final_answer":
                (
                    "Supervisor 无法完成"
                    "本次请求。"

                    f"\n错误："
                    f"{state.get('error')}"
                ),

            "status":
                "failed",
        }