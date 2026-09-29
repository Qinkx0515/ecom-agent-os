from collections.abc import Iterable

from fastapi import (
    FastAPI,
    HTTPException,
)
from fastapi.sse import (
    EventSourceResponse,
    ServerSentEvent,
)

from ecom_agent_os.api.runtime import (
    get_thread_summary,
    stream_new_request,
    stream_resume_request,
)
from ecom_agent_os.api.schemas import (
    ApprovalRequest,
    ChatRequest,
    HealthResponse,
    ThreadResponse,
)

app = FastAPI(
    title="CommercePilot API",
    description=(
        "Production-oriented "
        "e-commerce Multi-Agent API"
    ),
    version="0.9.0",
)


@app.get(
    "/health",
    response_model=HealthResponse,
)
def health():

    return HealthResponse(
        status="ok",
        service="CommercePilot",
        version="0.9.0",
    )

@app.post(
    "/api/v1/chat/stream",
    response_class=EventSourceResponse,
)
def chat_stream(
    body: ChatRequest,
) -> Iterable[ServerSentEvent]:

    for event in stream_new_request(
        body.request
    ):

        yield event.to_sse()


@app.post(
    "/api/v1/approve/stream",
    response_class=EventSourceResponse,
)
def approve_stream(
    body: ApprovalRequest,
) -> Iterable[ServerSentEvent]:

    for event in (
        stream_resume_request(
            thread_id=(
                body.thread_id
            ),
            decision=(
                body.decision
            ),
            comment=(
                body.comment
            ),
        )
    ):

        yield event.to_sse()


@app.get(
    "/api/v1/threads/{thread_id}",
    response_model=ThreadResponse,
)
def thread_status(
    thread_id: str,
):

    try:

        result = (
            get_thread_summary(
                thread_id
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


    return ThreadResponse(
        **result
    )