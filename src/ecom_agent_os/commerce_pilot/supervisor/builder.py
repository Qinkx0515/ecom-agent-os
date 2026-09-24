from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from ecom_agent_os.commerce_pilot.supervisor.dependencies import (
    SupervisorDependencies,
)
from ecom_agent_os.commerce_pilot.supervisor.nodes import (
    SupervisorNodes,
)
from ecom_agent_os.commerce_pilot.supervisor.routes import (
    route_supervisor,
)
from ecom_agent_os.commerce_pilot.supervisor.state import (
    SupervisorState,
)


def build_supervisor_graph(
    deps: (
        SupervisorDependencies
        | None
    ) = None,
    checkpointer=None,
):

    if deps is None:

        deps = (
            SupervisorDependencies()
        )


    nodes = SupervisorNodes(
        deps
    )


    builder = StateGraph(
        SupervisorState
    )


    builder.add_node(
        "supervisor",
        nodes.supervisor,
    )


    builder.add_node(
        "analytics_agent",
        nodes.analytics_agent,
    )


    builder.add_node(
        "action_agent",
        nodes.action_agent,
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
        "supervisor",
    )


    builder.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "analytics_agent":
                "analytics_agent",

            "action_agent":
                "action_agent",

            "unsupported":
                "unsupported",

            "failed":
                "failed",
        },
    )


    builder.add_edge(
        "analytics_agent",
        END,
    )


    builder.add_edge(
        "action_agent",
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