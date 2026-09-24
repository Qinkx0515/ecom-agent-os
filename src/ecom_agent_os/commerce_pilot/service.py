from uuid import uuid4

from langfuse import (
    get_client,
    observe,
)

from ecom_agent_os.commerce_pilot.supervisor.builder import (
    build_supervisor_graph,
)
from ecom_agent_os.commerce_pilot.workflow.persistence import (
    create_sqlite_checkpointer,
)


@observe(
    name="commercepilot.request"
)
def run_commercepilot_request(
    request: str,
    thread_id: str | None = None,
):

    if thread_id is None:

        thread_id = (
            f"commerce-{uuid4()}"
        )


    langfuse = get_client()


    langfuse.update_current_span(
        metadata={
            "thread_id":
                thread_id,

            "application":
                "CommercePilot",

            "version":
                "v8",
        }
    )


    config = {
        "configurable": {
            "thread_id":
                thread_id
        }
    }


    with create_sqlite_checkpointer() as saver:

        graph = build_supervisor_graph(
            checkpointer=saver
        )


        result = graph.invoke(
            {
                "request":
                    request
            },
            config=config,
            durability="sync",
            version="v2",
        )

        state = result.value


        langfuse.update_current_span(
            metadata={
                "thread_id":
                    thread_id,

                "route":
                    state.get(
                        "route"
                    ),

                "agent_used":
                    state.get(
                        "agent_used"
                    ),

                "status":
                    state.get(
                        "status"
                    ),
            },

            output={
                "status":
                    state.get(
                        "status"
                    ),

                "route":
                    state.get(
                        "route"
                    ),

                "agent_used":
                    state.get(
                        "agent_used"
                    ),
            },
        )


    return {
        "thread_id":
            thread_id,

        "value":
            result.value,

        "interrupts":
            result.interrupts,
    }