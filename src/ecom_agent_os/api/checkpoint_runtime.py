import os

from langgraph.checkpoint.postgres.aio import (
    AsyncPostgresSaver,
)
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool


def get_checkpoint_database_url() -> str:

    url = os.getenv("CHECKPOINT_DATABASE_URL")

    if not url:
        raise RuntimeError("CHECKPOINT_DATABASE_URL is not configured.")

    return url


def create_checkpoint_pool() -> AsyncConnectionPool:

    return AsyncConnectionPool(
        conninfo=(get_checkpoint_database_url()),
        min_size=1,
        max_size=10,
        open=False,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        },
    )


def create_postgres_checkpointer(
    pool: AsyncConnectionPool,
) -> AsyncPostgresSaver:

    return AsyncPostgresSaver(pool)
