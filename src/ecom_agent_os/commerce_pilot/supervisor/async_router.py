import json

from langfuse import observe
from pydantic import ValidationError

from ecom_agent_os.commerce_pilot.llm.async_client import (
    get_async_llm_client,
    get_async_model_name,
)
from ecom_agent_os.commerce_pilot.supervisor.models import (
    SupervisorDecision,
)
from ecom_agent_os.commerce_pilot.supervisor.router import (
    SUPERVISOR_SYSTEM_PROMPT,
    SupervisorRoutingError,
)


@observe(name="supervisor.route")
async def async_route_request(
    request: str,
) -> SupervisorDecision:

    client = get_async_llm_client()

    try:
        response = await client.chat.completions.create(
            model=(get_async_model_name()),
            messages=[
                {
                    "role": "system",
                    "content": SUPERVISOR_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": request,
                },
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=300,
        )

    except Exception as exc:
        raise SupervisorRoutingError(f"Supervisor routing failed: {exc}") from exc

    content = response.choices[0].message.content

    if not content:
        raise SupervisorRoutingError("Supervisor returned empty content.")

    try:
        return SupervisorDecision.model_validate(json.loads(content))

    except (
        json.JSONDecodeError,
        ValidationError,
    ) as exc:
        raise SupervisorRoutingError(f"Invalid supervisor output: {exc}") from exc
