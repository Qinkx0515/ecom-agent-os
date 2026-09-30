from dataclasses import dataclass
from typing import Callable

from ecom_agent_os.commerce_pilot.sql.executor import (
    SQLExecutionResult,
    execute_safe_sql,
)
from ecom_agent_os.commerce_pilot.sql.schema_inspector import (
    format_schema_for_llm,
)
from ecom_agent_os.commerce_pilot.text_to_sql.answer_generator import (
    generate_answer,
)
from ecom_agent_os.commerce_pilot.text_to_sql.generator import (
    generate_sql,
)
from ecom_agent_os.commerce_pilot.text_to_sql.models import (
    SQLGeneration,
)


@dataclass(
    frozen=True,
)
class CommerceDependencies:
    schema_provider: Callable[
        [],
        str,
    ] = format_schema_for_llm

    sql_generator: Callable[
        ...,
        SQLGeneration,
    ] = generate_sql

    sql_executor: Callable[
        [str],
        SQLExecutionResult,
    ] = execute_safe_sql

    answer_generator: Callable[
        ...,
        str,
    ] = generate_answer
