from dataclasses import dataclass
from typing import (
    Awaitable,
    Callable,
)

from ecom_agent_os.commerce_pilot.sql.async_executor import (
    async_execute_safe_sql,
)
from ecom_agent_os.commerce_pilot.sql.async_schema_inspector import (
    async_format_schema_for_llm,
)
from ecom_agent_os.commerce_pilot.sql.executor import (
    SQLExecutionResult,
)
from ecom_agent_os.commerce_pilot.text_to_sql.async_answer_generator import (
    async_generate_answer,
)
from ecom_agent_os.commerce_pilot.text_to_sql.async_generator import (
    async_generate_sql,
)
from ecom_agent_os.commerce_pilot.text_to_sql.models import (
    SQLGeneration,
)


@dataclass(
    frozen=True,
)
class AsyncCommerceDependencies:

    schema_provider: Callable[
        [],
        Awaitable[str],
    ] = (
        async_format_schema_for_llm
    )


    sql_generator: Callable[
        ...,
        Awaitable[
            SQLGeneration
        ],
    ] = async_generate_sql


    sql_executor: Callable[
        [str],
        Awaitable[
            SQLExecutionResult
        ],
    ] = async_execute_safe_sql


    answer_generator: Callable[
        ...,
        Awaitable[str],
    ] = async_generate_answer