from dataclasses import dataclass
from typing import Callable

from ecom_agent_os.commerce_pilot.sql.executor import (
    SQLExecutionError,
    SQLExecutionResult,
    execute_safe_sql,
)
from ecom_agent_os.commerce_pilot.sql.schema_inspector import (
    format_schema_for_llm,
)
from ecom_agent_os.commerce_pilot.sql.validator import (
    SQLValidationError,
)
from ecom_agent_os.commerce_pilot.text_to_sql.answer_generator import (
    generate_answer,
)
from ecom_agent_os.commerce_pilot.text_to_sql.generator import (
    LLMGenerationError,
    generate_sql,
)
from ecom_agent_os.commerce_pilot.text_to_sql.models import (
    SQLGeneration,
)


@dataclass
class AttemptRecord:
    attempt: int

    sql: str | None

    query_plan: list[str]

    error: str | None


@dataclass
class TextToSQLResult:
    question: str

    sql: str

    query_plan: list[str]

    rows: list[dict]

    answer: str

    attempts: list[AttemptRecord]

    truncated: bool


class UnsupportedQuestionError(ValueError):
    pass


class TextToSQLFailed(RuntimeError):
    pass


def run_text_to_sql(
    question: str,
    max_attempts: int = 3,
    sql_generator: Callable = generate_sql,
    sql_executor: Callable = execute_safe_sql,
    answer_generator: Callable = generate_answer,
) -> TextToSQLResult:

    schema = format_schema_for_llm()

    previous_sql: str | None = None

    error_message: str | None = None

    attempts: list[AttemptRecord] = []

    for attempt_number in range(
        1,
        max_attempts + 1,
    ):
        try:
            generation: SQLGeneration = sql_generator(
                question=question,
                schema=schema,
                previous_sql=previous_sql,
                error_message=error_message,
            )

        except LLMGenerationError as exc:
            attempts.append(
                AttemptRecord(
                    attempt=attempt_number,
                    sql=None,
                    query_plan=[],
                    error=str(exc),
                )
            )

            error_message = str(exc)

            continue

        if not generation.is_supported:
            raise UnsupportedQuestionError(
                generation.unsupported_reason or "Unsupported question."
            )

        sql = generation.sql

        assert sql is not None

        try:
            execution: SQLExecutionResult = sql_executor(sql)

        except (
            SQLValidationError,
            SQLExecutionError,
        ) as exc:
            error_message = str(exc)[:1500]

            previous_sql = sql

            attempts.append(
                AttemptRecord(
                    attempt=attempt_number,
                    sql=sql,
                    query_plan=generation.query_plan,
                    error=error_message,
                )
            )

            continue

        attempts.append(
            AttemptRecord(
                attempt=attempt_number,
                sql=execution.sql,
                query_plan=generation.query_plan,
                error=None,
            )
        )

        answer = answer_generator(
            question=question,
            result=execution,
        )

        return TextToSQLResult(
            question=question,
            sql=execution.sql,
            query_plan=generation.query_plan,
            rows=execution.rows,
            answer=answer,
            attempts=attempts,
            truncated=execution.truncated,
        )

    raise TextToSQLFailed(
        f"Text-to-SQL failed after {max_attempts} attempts. Last error: {error_message}"
    )
