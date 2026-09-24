from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ecom_agent_os.database.session import engine

from ecom_agent_os.commerce_pilot.sql.validator import (
    MAX_RESULT_ROWS,
    SQLValidationError,
    validate_sql,
)

import time

from langfuse import (
    get_client,
    observe,
)

@dataclass
class SQLExecutionResult:

    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    truncated: bool
    sql: str


class SQLExecutionError(
    RuntimeError
):
    pass


@observe(
    name="sql.execute",
    capture_input=False,
    capture_output=False,
)
def execute_safe_sql(
    sql: str,
    max_rows: int = MAX_RESULT_ROWS,
) -> SQLExecutionResult:

    start = (
        time.perf_counter()
    )

    validation = validate_sql(
        sql
    )

    safe_sql = validation.sql

    try:

        with engine.connect() as connection:

            transaction = (
                connection.begin()
            )

            try:

                connection.execute(
                    text(
                        "SET TRANSACTION "
                        "READ ONLY"
                    )
                )

                connection.execute(
                    text(
                        "SET LOCAL "
                        "statement_timeout "
                        "= '5000ms'"
                    )
                )

                result = (
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

                transaction.commit()

            except Exception:

                transaction.rollback()

                raise

    except (
        SQLValidationError
    ):
        raise

    except SQLAlchemyError as exc:

        raise SQLExecutionError(
            f"Database execution "
            f"failed: {exc}"
        ) from exc


    latency_ms = (
        time.perf_counter()
        - start
    ) * 1000


    langfuse = get_client()


    langfuse.update_current_span(
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
        row_count=len(rows),
        truncated=truncated,
        sql=safe_sql,
    )

