from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from ecom_agent_os.commerce_pilot.workflow.dependencies import (
    CommerceDependencies,
)
from ecom_agent_os.commerce_pilot.workflow.nodes import (
    CommerceNodes,
)
from ecom_agent_os.commerce_pilot.workflow.routes import (
    route_after_execution,
    route_after_generation,
    route_retry,
)
from ecom_agent_os.commerce_pilot.workflow.state import (
    CommerceGraphState,
)


def build_commerce_graph(
    deps: CommerceDependencies | None = None,
    checkpointer=None,
):

    if deps is None:

        deps = CommerceDependencies()

    nodes = CommerceNodes(
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
        {
            "execute_sql":
                "execute_sql",

            "retry_or_fail":
                "retry_or_fail",

            "unsupported":
                "unsupported",
        },
    )

    builder.add_conditional_edges(
        "execute_sql",
        route_after_execution,
        {
            "generate_answer":
                "generate_answer",

            "retry_or_fail":
                "retry_or_fail",
        },
    )

    builder.add_conditional_edges(
        "retry_or_fail",
        route_retry,
        {
            "generate_sql":
                "generate_sql",

            "failed":
                "failed",
        },
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

    return builder.compile(
        checkpointer=checkpointer
    )


# if __name__ == "__main__":
#
#     graph = build_commerce_graph()
#
#     print(
#         graph
#         .get_graph()
#         .draw_mermaid()
#     )