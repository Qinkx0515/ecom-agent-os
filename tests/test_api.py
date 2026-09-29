from fastapi.testclient import (
    TestClient,
)

from ecom_agent_os.api.app import (
    app,
)


client = TestClient(
    app
)


def test_health():

    response = client.get(
        "/health"
    )

    assert (
        response.status_code
        == 200
    )

    data = response.json()

    assert (
        data["status"]
        == "ok"
    )

    assert (
        data["service"]
        == "CommercePilot"
    )


from ecom_agent_os.api.events import (
    AgentEvent,
)


def test_agent_event_creation():

    event = AgentEvent(
        event="started",
        event_id="thread-1:1",
        data={
            "thread_id":
                "thread-1"
        },
    )

    sse = event.to_sse()

    assert (
        sse.event
        == "started"
    )

    assert (
        sse.id
        == "thread-1:1"
    )