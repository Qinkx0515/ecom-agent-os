from contextlib import asynccontextmanager

from fastapi import FastAPI

from ecom_agent_os.api.checkpoint_runtime import (
    create_checkpoint_pool,
    create_postgres_checkpointer,
)
from ecom_agent_os.commerce_pilot.supervisor.builder import (
    build_supervisor_graph,
)
from collections.abc import (
    AsyncIterable,
)

from fastapi import (
    Request,
)

from fastapi.sse import (
    EventSourceResponse,
    ServerSentEvent,
)

from ecom_agent_os.api.runtime_v10 import (
    get_thread_summary_v10,
    stream_new_request_v10,
    stream_resume_request_v10,
)

from ecom_agent_os.api.schemas import (
    ApprovalRequest,
    ChatRequest,
    ThreadResponse,
)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):

    pool = create_checkpoint_pool()

    await pool.open()

    checkpointer = (
        create_postgres_checkpointer(
            pool
        )
    )

    await checkpointer.setup()

    graph = build_supervisor_graph(
        checkpointer=checkpointer
    )

    app.state.checkpoint_pool = pool

    app.state.checkpointer = (
        checkpointer
    )

    app.state.commerce_graph = (
        graph
    )

    try:

        yield

    finally:

        await pool.close()


app = FastAPI(
    title="CommercePilot API",
    description=(
        "Production-oriented "
        "e-commerce Multi-Agent API"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

@app.get("/health")
async def health():

    return {
        "status": "ok",
        "service": "CommercePilot",
        "version": "1.0.0",
        "checkpoint_backend":
            "postgresql",
    }

@app.post(
    "/api/v1/chat/stream",
    response_class=EventSourceResponse,
)
async def chat_stream(
    body: ChatRequest,
    request: Request,
) -> AsyncIterable[
    ServerSentEvent
]:

    graph = (
        request.app.state
        .commerce_graph
    )


    async for event in (
        stream_new_request_v10(
            graph,
            body.request,
        )
    ):

        yield event.to_sse()

@app.post(
    "/api/v1/approve/stream",
    response_class=EventSourceResponse,
)
async def approve_stream(
    body: ApprovalRequest,
    request: Request,
) -> AsyncIterable[
    ServerSentEvent
]:

    graph = (
        request.app.state
        .commerce_graph
    )


    async for event in (
        stream_resume_request_v10(
            graph=graph,

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
async def thread_status(
    thread_id: str,
    request: Request,
):

    graph = (
        request.app.state
        .commerce_graph
    )


    result = (
        await get_thread_summary_v10(
            graph,
            thread_id,
        )
    )


    return ThreadResponse(
        **result
    )