import json

from pydantic import ValidationError

from ecom_agent_os.commerce_pilot.llm.client import (
    get_llm_client,
    get_model_name,
)
from ecom_agent_os.commerce_pilot.supervisor.models import (
    SupervisorDecision,
)


class SupervisorRoutingError(
    RuntimeError
):
    pass


SUPERVISOR_SYSTEM_PROMPT = """
You are the routing supervisor of CommercePilot,
an e-commerce operations multi-agent system.

There are currently two specialized agents.

1. analytics
   Handles READ-ONLY business analytics questions.
   Examples:
   - GMV
   - sales
   - orders
   - traffic
   - conversion rate
   - refunds
   - category performance
   - historical comparisons

2. action
   Handles business requests that MODIFY system data.
   Currently supported write action:
   - update one product's price

3. unsupported
   Use this when the request belongs to neither capability.

Routing principles:

- Questions asking to inspect, calculate, compare,
  explain or analyze business data -> analytics.

- Requests asking the system to change product data
  -> action.

- Never execute the request yourself.
- Only decide which specialized agent should handle it.
- Return JSON only.

Required format:

{
  "route": "analytics",
  "confidence": 0.95,
  "reason": "short reason"
}
"""


def route_request(
    request: str,
) -> SupervisorDecision:

    client = get_llm_client()

    try:

        response = (
            client.chat.completions.create(
                model=get_model_name(),
                messages=[
                    {
                        "role": "system",
                        "content":
                            SUPERVISOR_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content":
                            request,
                    },
                ],
                response_format={
                    "type":
                        "json_object"
                },
                temperature=0,
                max_tokens=300,
            )
        )

    except Exception as exc:

        raise SupervisorRoutingError(
            f"Supervisor routing "
            f"failed: {exc}"
        ) from exc


    content = (
        response
        .choices[0]
        .message
        .content
    )


    if not content:

        raise SupervisorRoutingError(
            "Supervisor returned "
            "empty content."
        )


    try:

        data = json.loads(
            content
        )

        return (
            SupervisorDecision
            .model_validate(
                data
            )
        )

    except (
        json.JSONDecodeError,
        ValidationError,
    ) as exc:

        raise SupervisorRoutingError(
            "Invalid supervisor "
            f"output: {exc}"
        ) from exc