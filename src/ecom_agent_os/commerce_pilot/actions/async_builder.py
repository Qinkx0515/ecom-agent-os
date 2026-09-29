from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from ecom_agent_os.commerce_pilot.actions.async_dependencies import (
    AsyncActionDependencies,
)
from ecom_agent_os.commerce_pilot.actions.async_nodes import (
    AsyncActionNodes,
)
from ecom_agent_os.commerce_pilot.actions.routes import (
    route_after_approval,
    route_after_plan,
    route_after_product,
    route_after_risk,
)
from ecom_agent_os.commerce_pilot.actions.state import (
    ActionState,
)


def build_async_action_graph(
    deps: AsyncActionDependencies | None = None,
    checkpointer=None,
):

    if deps is None:

        deps = AsyncActionDependencies()


    nodes = AsyncActionNodes(
        deps
    )


    builder = StateGraph(
        ActionState
    )


    builder.add_node(
        "plan_action",
        nodes.plan_action,
    )

    builder.add_node(
        "load_product",
        nodes.load_product,
    )

    builder.add_node(
        "assess_risk",
        nodes.assess_risk,
    )

    builder.add_node(
        "human_approval",
        nodes.human_approval,
    )

    builder.add_node(
        "execute_action",
        nodes.execute_action,
    )

    builder.add_node(
        "rejected",
        nodes.rejected,
    )

    builder.add_node(
        "unsupported",
        nodes.unsupported,
    )

    builder.add_node(
        "failed",
        nodes.failed,
    )


    builder.add_edge(
        START,
        "plan_action",
    )


    builder.add_conditional_edges(
        "plan_action",
        route_after_plan,
        {
            "load_product":
                "load_product",

            "unsupported":
                "unsupported",

            "failed":
                "failed",
        },
    )


    builder.add_conditional_edges(
        "load_product",
        route_after_product,
        {
            "assess_risk":
                "assess_risk",

            "failed":
                "failed",
        },
    )


    builder.add_conditional_edges(
        "assess_risk",
        route_after_risk,
        {
            "human_approval":
                "human_approval",

            "failed":
                "failed",
        },
    )


    builder.add_conditional_edges(
        "human_approval",
        route_after_approval,
        {
            "execute_action":
                "execute_action",

            "rejected":
                "rejected",
        },
    )


    builder.add_edge(
        "execute_action",
        END,
    )

    builder.add_edge(
        "rejected",
        END,
    )

    builder.add_edge(
        "unsupported",
        END,
    )

    builder.add_edge(
        "failed",
        END,
    )


    return builder.compile(
        checkpointer=checkpointer
    )