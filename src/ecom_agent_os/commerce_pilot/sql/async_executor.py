import time
from typing import Any

from langfuse import (
    get_client,
    observe,
)
from sqlalchemy import text
from sqlalchemy.exc import (
    SQLAlchemyError,
)

from ecom_agent_os.database.async_session import (
    async_engine,
)
from ecom_agent_os.commerce_pilot.sql.executor import (
    SQLExecutionError,
    SQLExecutionResult,
)
from ecom_agent_os.commerce_pilot.sql.validator import (
    MAX_RESULT_ROWS,
    validate_sql,
)


@observe(
    name="sql.execute",
    capture_input=False,
    capture_output=False,
)
async def async_execute_safe_sql(
    sql: str,
    max_rows: int = MAX_RESULT_ROWS,
) -> SQLExecutionResult:

    start = (
        time.perf_counter()
    )


    # CPU-only，保留同步即可
    validation = validate_sql(
        sql
    )

    safe_sql = validation.sql


    try:

        async with (
            async_engine.connect()
        ) as connection:

            async with (
                connection.begin()
            ):

                await connection.execute(
                    text(
                        "SET TRANSACTION "
                        "READ ONLY"
                    )
                )

                await connection.execute(
                    text(
                        "SET LOCAL "
                        "statement_timeout "
                        "= '5000ms'"
                    )
                )

                result = await (
                    connection.execute(
                        text(
                            safe_sql
                        )
                    )
                )


                rows = (
                    result
                    .mappings()
                    .fetchmany(
                        max_rows + 1
                    )
                )


                truncated = (
                    len(rows)
                    > max_rows
                )


                rows = rows[
                    :max_rows
                ]


                columns = list(
                    result.keys()
                )


    except SQLAlchemyError as exc:

        raise SQLExecutionError(
            "Database execution "
            f"failed: {exc}"
        ) from exc


    latency_ms = (
        (
            time.perf_counter()
            - start
        )
        * 1000
    )


    get_client().update_current_span(
        metadata={
            "tables":
                sorted(
                    validation.tables
                ),

            "row_count":
                len(rows),

            "truncated":
                truncated,

            "latency_ms":
                round(
                    latency_ms,
                    2,
                ),

            "runtime":
                "async",
        },
        output={
            "row_count":
                len(rows),

            "truncated":
                truncated,
        },
    )


    return SQLExecutionResult(
        columns=columns,

        rows=[
            dict(row)
            for row in rows
        ],

        row_count=len(
            rows
        ),

        truncated=truncated,

        sql=safe_sql,
    )