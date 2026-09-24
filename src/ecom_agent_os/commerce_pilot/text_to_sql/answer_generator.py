import json
from datetime import (
    date,
    datetime,
)
from decimal import Decimal
from typing import Any

from ecom_agent_os.commerce_pilot.llm.client import (
    get_llm_client,
    get_model_name,
)
from ecom_agent_os.commerce_pilot.sql.executor import (
    SQLExecutionResult,
)
from langfuse import observe

class AnswerGenerationError(
    RuntimeError
):
    pass


def make_json_safe(
    value: Any,
):

    if isinstance(
        value,
        Decimal,
    ):
        return str(value)

    if isinstance(
        value,
        (date, datetime),
    ):
        return value.isoformat()

    return value


def serialize_rows(
    rows: list[dict],
) -> list[dict]:

    return [
        {
            key: make_json_safe(value)
            for key, value in row.items()
        }
        for row in rows
    ]


@observe(
    name="answer.generate"
)
def generate_answer(
    question: str,
    result: SQLExecutionResult,
) -> str:

    client = get_llm_client()

    rows = serialize_rows(
        result.rows[:50]
    )

    result_json = json.dumps(
        rows,
        ensure_ascii=False,
        indent=2,
    )

    system_prompt = """
You are CommercePilot's analytics answer agent.

Answer the user's question using ONLY the provided
database query result.

Rules:

1. Never invent numbers.
2. Never claim something that is not supported by the data.
3. If the result is insufficient, explicitly say so.
4. Keep the answer concise and business-oriented.
5. Use Chinese.
"""

    user_prompt = f"""
用户问题：

{question}

实际执行的 SQL：

{result.sql}

数据库返回结果：

{result_json}

请基于这些数据回答用户问题。
"""

    try:

        response = (
            client.chat.completions.create(
                model=get_model_name(),
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                temperature=0,
                max_tokens=800,
            )
        )

    except Exception as exc:

        raise AnswerGenerationError(
            f"Answer generation failed: {exc}"
        ) from exc

    content = (
        response
        .choices[0]
        .message
        .content
    )

    if not content:

        raise AnswerGenerationError(
            "Answer model returned "
            "empty content."
        )

    return content.strip()