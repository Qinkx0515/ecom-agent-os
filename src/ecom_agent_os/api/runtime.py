from collections.abc import Iterator
from uuid import uuid4

from langgraph.types import (
    Command,
)

from ecom_agent_os.api.events import (
    AgentEvent,
)
from ecom_agent_os.commerce_pilot.supervisor.builder import (
    build_supervisor_graph,
)
from ecom_agent_os.commerce_pilot.workflow.persistence import (
    create_sqlite_checkpointer,
)
import os

NODE_EVENT_NAMES = {

    "supervisor":
        "supervisor_routed",

    "generate_sql":
        "sql_generated",

    "execute_sql":
        "sql_executed",

    "generate_answer":
        "answer_generated",

    "plan_action":
        "action_planned",

    "load_product":
        "product_loaded",

    "assess_risk":
        "risk_assessed",

    "execute_action":
        "action_executed",

    "rejected":
        "action_rejected",

    "unsupported":
        "unsupported",

    "failed":
        "node_failed",
}


def project_node_update(
    node_name: str,
    update: object,
) -> dict:

    if not isinstance(
        update,
        dict,
    ):

        return {}


    if node_name == "supervisor":

        return {
            "route":
                update.get(
                    "route"
                ),

            "confidence":
                update.get(
                    "route_confidence"
                ),

            "reason":
                update.get(
                    "route_reason"
                ),
        }


    if node_name == "generate_sql":

        return {
            "attempt":
                update.get(
                    "attempt_number"
                ),

            "query_plan":
                update.get(
                    "query_plan",
                    [],
                ),

            "sql":
                update.get(
                    "current_sql"
                ),

            "status":
                update.get(
                    "status"
                ),
        }


    if node_name == "execute_sql":

        rows = update.get(
            "rows",
            [],
        )

        return {
            "success":
                update.get(
                    "execution_ok"
                ),

            "row_count":
                len(rows),

            "truncated":
                update.get(
                    "truncated",
                    False,
                ),

            "status":
                update.get(
                    "status"
                ),

            "error":
                update.get(
                    "last_error"
                ),
        }


    if node_name == "generate_answer":

        return {
            "status":
                update.get(
                    "status"
                ),
        }


    if node_name == "plan_action":

        return {
            "action_id":
                update.get(
                    "action_id"
                ),

            "action_type":
                update.get(
                    "action_type"
                ),

            "sku":
                update.get(
                    "sku"
                ),

            "new_price":
                update.get(
                    "new_price"
                ),

            "status":
                update.get(
                    "status"
                ),
        }


    if node_name == "load_product":

        return {
            "sku":
                update.get(
                    "sku"
                ),

            "product_name":
                update.get(
                    "product_name"
                ),

            "old_price":
                update.get(
                    "old_price"
                ),

            "status":
                update.get(
                    "status"
                ),
        }


    if node_name == "assess_risk":

        return {
            "risk_level":
                update.get(
                    "risk_level"
                ),

            "price_change_pct":
                update.get(
                    "price_change_pct"
                ),

            "approval_required":
                update.get(
                    "approval_required"
                ),
        }


    if node_name == "execute_action":

        return {
            "status":
                update.get(
                    "status"
                ),

            "result":
                update.get(
                    "action_result"
                ),

            "error":
                update.get(
                    "error"
                ),
        }


    return {
        "status":
            update.get(
                "status"
            )
    }


def serialize_interrupt(
    interrupt_item,
) -> dict:

    return {
        "interrupt_id":
            getattr(
                interrupt_item,
                "id",
                None,
            ),

        "approval":
            getattr(
                interrupt_item,
                "value",
                None,
            ),
    }


def stream_new_request(
    request: str,
) -> Iterator[AgentEvent]:

    thread_id = (
        f"commerce-{uuid4()}"
    )


    config = {
        "configurable": {
            "thread_id":
                thread_id
        }
    }


    sequence = 1


    yield AgentEvent(
        event="started",
        event_id=(
            f"{thread_id}:"
            f"{sequence}"
        ),
        data={
            "thread_id":
                thread_id,
        },
    )


    sequence += 1


    with create_sqlite_checkpointer() as saver:

        graph = (
            build_supervisor_graph(
                checkpointer=saver
            )
        )


        try:

            for part in graph.stream(
                {
                    "request":
                        request
                },
                config=config,
                stream_mode="updates",
                subgraphs=True,
                durability="sync",
                version="v2",
            ):

                if (
                    part.get(
                        "type"
                    )
                    != "updates"
                ):

                    continue


                namespace = list(
                    part.get(
                        "ns",
                        (),
                    )
                )


                updates = (
                    part.get(
                        "data",
                        {}
                    )
                )


                interrupts = (
                    updates.get(
                        "__interrupt__"
                    )
                )


                if interrupts:

                    for interrupt_item in (
                        interrupts
                    ):

                        payload = (
                            serialize_interrupt(
                                interrupt_item
                            )
                        )

                        payload[
                            "thread_id"
                        ] = thread_id


                        yield AgentEvent(
                            event=(
                                "approval_required"
                            ),
                            event_id=(
                                f"{thread_id}:"
                                f"{sequence}"
                            ),
                            data=payload,
                        )

                        sequence += 1


                    return


                for (
                    node_name,
                    update,
                ) in updates.items():

                    if node_name.startswith(
                        "__"
                    ):

                        continue


                    event_name = (
                        NODE_EVENT_NAMES.get(
                            node_name,
                            "node_update",
                        )
                    )


                    payload = (
                        project_node_update(
                            node_name,
                            update,
                        )
                    )


                    payload[
                        "node"
                    ] = node_name

                    payload[
                        "namespace"
                    ] = namespace


                    yield AgentEvent(
                        event=event_name,
                        event_id=(
                            f"{thread_id}:"
                            f"{sequence}"
                        ),
                        data=payload,
                    )

                    sequence += 1


            snapshot = (
                graph.get_state(
                    config
                )
            )


            state = (
                snapshot.values
            )


            yield AgentEvent(
                event="completed",
                event_id=(
                    f"{thread_id}:"
                    f"{sequence}"
                ),
                data={
                    "thread_id":
                        thread_id,

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

                    "answer":
                        state.get(
                            "final_answer"
                        ),
                },
            )


        except Exception as exc:

            yield AgentEvent(
                event="error",
                event_id=(
                    f"{thread_id}:"
                    f"{sequence}"
                ),
                data={
                    "thread_id":
                        thread_id,

                    "message":
                        "CommercePilot "
                        "request failed.",

                    # 开发阶段暂时保留
                    "detail":
                        public_error_detail(
                            exc
                        ),
                },
            )


def stream_resume_request(
    thread_id: str,
    decision: str,
    comment: str | None,
) -> Iterator[AgentEvent]:

    config = {
        "configurable": {
            "thread_id":
                thread_id
        }
    }


    sequence = 1


    yield AgentEvent(
        event="approval_resumed",
        event_id=(
            f"{thread_id}:resume:"
            f"{sequence}"
        ),
        data={
            "thread_id":
                thread_id,

            "decision":
                decision,
        },
    )


    sequence += 1


    resume_value = {
        "decision":
            decision,

        "comment":
            comment,
    }


    with create_sqlite_checkpointer() as saver:

        graph = (
            build_supervisor_graph(
                checkpointer=saver
            )
        )


        try:

            for part in graph.stream(
                Command(
                    resume=resume_value
                ),
                config=config,
                stream_mode="updates",
                subgraphs=True,
                durability="sync",
                version="v2",
            ):

                if (
                    part.get(
                        "type"
                    )
                    != "updates"
                ):

                    continue


                namespace = list(
                    part.get(
                        "ns",
                        (),
                    )
                )


                updates = part.get(
                    "data",
                    {},
                )


                interrupts = (
                    updates.get(
                        "__interrupt__"
                    )
                )


                if interrupts:

                    for interrupt_item in (
                        interrupts
                    ):

                        payload = (
                            serialize_interrupt(
                                interrupt_item
                            )
                        )

                        payload[
                            "thread_id"
                        ] = thread_id


                        yield AgentEvent(
                            event=(
                                "approval_required"
                            ),
                            event_id=(
                                f"{thread_id}:"
                                f"resume:"
                                f"{sequence}"
                            ),
                            data=payload,
                        )

                        sequence += 1


                    return


                for (
                    node_name,
                    update,
                ) in updates.items():

                    if node_name.startswith(
                        "__"
                    ):

                        continue


                    payload = (
                        project_node_update(
                            node_name,
                            update,
                        )
                    )

                    payload[
                        "node"
                    ] = node_name

                    payload[
                        "namespace"
                    ] = namespace


                    yield AgentEvent(
                        event=(
                            NODE_EVENT_NAMES.get(
                                node_name,
                                "node_update",
                            )
                        ),
                        event_id=(
                            f"{thread_id}:"
                            f"resume:"
                            f"{sequence}"
                        ),
                        data=payload,
                    )

                    sequence += 1


            snapshot = (
                graph.get_state(
                    config
                )
            )

            state = (
                snapshot.values
            )


            yield AgentEvent(
                event="completed",
                event_id=(
                    f"{thread_id}:"
                    f"resume:"
                    f"{sequence}"
                ),
                data={
                    "thread_id":
                        thread_id,

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

                    "answer":
                        state.get(
                            "final_answer"
                        ),
                },
            )


        except Exception as exc:

            yield AgentEvent(
                event="error",
                event_id=(
                    f"{thread_id}:"
                    f"resume:"
                    f"{sequence}"
                ),
                data={
                    "thread_id":
                        thread_id,

                    "message":
                        "Approval resume "
                        "failed.",

                    "detail":
                        public_error_detail(
                            exc
                        ),
                },
            )


def get_thread_summary(
    thread_id: str,
) -> dict:

    config = {
        "configurable": {
            "thread_id":
                thread_id
        }
    }


    with create_sqlite_checkpointer() as saver:

        graph = (
            build_supervisor_graph(
                checkpointer=saver
            )
        )


        snapshot = (
            graph.get_state(
                config
            )
        )


        values = (
            snapshot.values
            or {}
        )


        return {
            "thread_id":
                thread_id,

            "status":
                values.get(
                    "status"
                ),

            "route":
                values.get(
                    "route"
                ),

            "agent_used":
                values.get(
                    "agent_used"
                ),

            "final_answer":
                values.get(
                    "final_answer"
                ),

            "next_nodes":
                list(
                    snapshot.next
                ),
        }

def public_error_detail(
    exc: Exception,
) -> str | None:

    app_env = os.getenv(
        "APP_ENV",
        "development",
    )

    if app_env == "development":

        return str(
            exc
        )

    return None

