from collections.abc import (
    AsyncIterator,
)
from typing import Any
from uuid import uuid4

from langgraph.types import Command

from ecom_agent_os.api.events import (
    AgentEvent,
)


def build_milestone_events(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> list[
    tuple[
        str,
        dict[str, Any],
    ]
]:

    events = []

    # ===== Supervisor =====

    if current.get("route") and current.get("route") != previous.get("route"):
        events.append(
            (
                "supervisor_routed",
                {
                    "route": current.get("route"),
                    "confidence": current.get("route_confidence"),
                    "reason": current.get("route_reason"),
                },
            )
        )

    # ===== SQL =====

    if current.get("current_sql") and current.get("current_sql") != previous.get(
        "current_sql"
    ):
        events.append(
            (
                "sql_generated",
                {
                    "attempt": current.get("attempt_number"),
                    "query_plan": current.get(
                        "query_plan",
                        [],
                    ),
                    "sql": current.get("current_sql"),
                },
            )
        )

    # ===== SQL Execution =====

    if current.get("execution_ok") is True and previous.get("execution_ok") is not True:
        events.append(
            (
                "sql_executed",
                {
                    "success": True,
                    "row_count": len(
                        current.get(
                            "rows",
                            [],
                        )
                    ),
                    "truncated": current.get(
                        "truncated",
                        False,
                    ),
                },
            )
        )

    # ===== Risk =====

    if current.get("risk_level") and current.get("risk_level") != previous.get(
        "risk_level"
    ):
        events.append(
            (
                "risk_assessed",
                {
                    "risk_level": current.get("risk_level"),
                    "price_change_pct": current.get("price_change_pct"),
                },
            )
        )

    return events


async def stream_new_request_v10(
    graph,
    request_text: str,
) -> AsyncIterator[AgentEvent]:

    thread_id = f"commerce-{uuid4()}"

    config = {"configurable": {"thread_id": thread_id}}

    sequence = 1

    yield AgentEvent(
        event="started",
        event_id=(f"{thread_id}:{sequence}"),
        data={
            "thread_id": thread_id,
        },
    )

    sequence += 1

    previous_state: dict = {}

    stream = await graph.astream_events(
        {"request": request_text},
        config=config,
        version="v3",
    )

    async for snapshot in stream.values:
        state = dict(snapshot)

        milestone_events = build_milestone_events(
            previous_state,
            state,
        )

        for (
            event_name,
            payload,
        ) in milestone_events:
            payload["thread_id"] = thread_id

            yield AgentEvent(
                event=event_name,
                event_id=(f"{thread_id}:{sequence}"),
                data=payload,
            )

            sequence += 1

        previous_state = state

    output = stream.output or previous_state or {}

    yield AgentEvent(
        event="completed",
        event_id=(f"{thread_id}:{sequence}"),
        data={
            "thread_id": thread_id,
            "status": output.get("status"),
            "route": output.get("route"),
            "agent_used": output.get("agent_used"),
            "answer": output.get("final_answer"),
        },
    )


async def stream_resume_request_v10(
    graph,
    thread_id: str,
    decision: str,
    comment: str | None,
) -> AsyncIterator[AgentEvent]:

    config = {"configurable": {"thread_id": thread_id}}

    sequence = 1

    yield AgentEvent(
        event="approval_resumed",
        event_id=(f"{thread_id}:resume:{sequence}"),
        data={
            "thread_id": thread_id,
            "decision": decision,
        },
    )

    sequence += 1

    stream = await graph.astream_events(
        Command(
            resume={
                "decision": decision,
                "comment": comment,
            }
        ),
        config=config,
        version="v3",
    )

    previous_state = {}

    async for snapshot in stream.values:
        state = dict(snapshot)

        for (
            event_name,
            payload,
        ) in build_milestone_events(
            previous_state,
            state,
        ):
            payload["thread_id"] = thread_id

            yield AgentEvent(
                event=event_name,
                event_id=(f"{thread_id}:resume:{sequence}"),
                data=payload,
            )

            sequence += 1

        previous_state = state

    if stream.interrupted:
        for interrupt_item in stream.interrupts:
            yield AgentEvent(
                event="approval_required",
                event_id=(f"{thread_id}:resume:{sequence}"),
                data={
                    "thread_id": thread_id,
                    "interrupt_id": getattr(
                        interrupt_item,
                        "id",
                        None,
                    ),
                    "approval": getattr(
                        interrupt_item,
                        "value",
                        None,
                    ),
                },
            )

        return

    output = stream.output or previous_state or {}

    yield AgentEvent(
        event="completed",
        event_id=(f"{thread_id}:resume:{sequence}"),
        data={
            "thread_id": thread_id,
            "status": output.get("status"),
            "route": output.get("route"),
            "agent_used": output.get("agent_used"),
            "answer": output.get("final_answer"),
        },
    )


async def get_thread_summary_v10(
    graph,
    thread_id: str,
) -> dict:

    config = {"configurable": {"thread_id": thread_id}}

    snapshot = await graph.aget_state(config)

    values = snapshot.values or {}

    return {
        "thread_id": thread_id,
        "status": values.get("status"),
        "route": values.get("route"),
        "agent_used": values.get("agent_used"),
        "final_answer": values.get("final_answer"),
        "next_nodes": list(snapshot.next),
    }
