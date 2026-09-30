import json

from langfuse import observe
from pydantic import ValidationError

from ecom_agent_os.commerce_pilot.llm.client import (
    get_llm_client,
    get_model_name,
)
from ecom_agent_os.commerce_pilot.text_to_sql.models import (
    SQLGeneration,
)
from ecom_agent_os.commerce_pilot.text_to_sql.prompts import (
    SQL_SYSTEM_PROMPT,
    build_sql_prompt,
)


class LLMGenerationError(RuntimeError):
    pass


@observe(name="text_to_sql.generate")
def generate_sql(
    question: str,
    schema: str,
    previous_sql: str | None = None,
    error_message: str | None = None,
) -> SQLGeneration:

    client = get_llm_client()

    prompt = build_sql_prompt(
        question=question,
        schema=schema,
        previous_sql=previous_sql,
        error_message=error_message,
    )

    try:
        response = client.chat.completions.create(
            model=get_model_name(),
            messages=[
                {
                    "role": "system",
                    "content": SQL_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=1200,
        )

    except Exception as exc:
        raise LLMGenerationError(f"LLM request failed: {exc}") from exc

    content = response.choices[0].message.content

    if not content:
        raise LLMGenerationError("LLM returned empty content.")

    try:
        data = json.loads(content)

        return SQLGeneration.model_validate(data)

    except (
        json.JSONDecodeError,
        ValidationError,
    ) as exc:
        raise LLMGenerationError(
            f"LLM returned invalid structured output: {exc}"
        ) from exc
