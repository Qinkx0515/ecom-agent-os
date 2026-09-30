import os
from langgraph.checkpoint.postgres.aio import (
    AsyncPostgresSaver,
)
import pytest


pytestmark = pytest.mark.integration

CHECKPOINT_DATABASE_URL = os.getenv("CHECKPOINT_DATABASE_URL")


@pytest.mark.skipif(
    not CHECKPOINT_DATABASE_URL,
    reason=("CHECKPOINT_DATABASE_URL not configured"),
)
@pytest.mark.asyncio
async def test_postgres_checkpointer():

    async with AsyncPostgresSaver.from_conn_string(CHECKPOINT_DATABASE_URL) as saver:
        await saver.setup()

        assert saver is not None
