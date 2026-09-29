from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from ecom_agent_os.commerce_pilot.workflow.async_dependencies import (
    AsyncCommerceDependencies,
)
from ecom_agent_os.commerce_pilot.workflow.async_nodes import (
    AsyncCommerceNodes,
)
from ecom_agent_os.commerce_pilot.workflow.routes import (
    route_after_execution,
    route_after_generation,
    route_retry,
)
from ecom_agent_os.commerce_pilot.workflow.state import (
    CommerceGraphState,
)


def build_async_commerce_graph(
    deps: (
        AsyncCommerceDependencies
        | None
    ) = None,
):

    if deps is None:

        deps = (
            AsyncCommerceDependencies()
        )


    nodes = AsyncCommerceNodes(
        deps
    )


    builder = StateGraph(
        CommerceGraphState
    )


    builder.add_node(
        "load_context",
        nodes.load_context,
    )

    builder.add_node(
        "generate_sql",
        nodes.generate_sql,
    )

    builder.add_node(
        "execute_sql",
        nodes.execute_sql,
    )

    builder.add_node(
        "retry_or_fail",
        nodes.retry_or_fail,
    )

    builder.add_node(
        "generate_answer",
        nodes.generate_answer,
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
        "load_context",
    )

    builder.add_edge(
        "load_context",
        "generate_sql",
    )


    builder.add_conditional_edges(
        "generate_sql",
        route_after_generation,
    )


    builder.add_conditional_edges(
        "execute_sql",
        route_after_execution,
    )


    builder.add_conditional_edges(
        "retry_or_fail",
        route_retry,
    )


    builder.add_edge(
        "generate_answer",
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


    return builder.compile()