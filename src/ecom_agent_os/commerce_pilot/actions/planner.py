import json

from pydantic import ValidationError

from ecom_agent_os.commerce_pilot.actions.models import (
    ActionPlan,
)
from ecom_agent_os.commerce_pilot.llm.client import (
    get_llm_client,
    get_model_name,
)
from langfuse import observe

class ActionPlanningError(
    RuntimeError
):
    pass


ACTION_SYSTEM_PROMPT = """
You are CommercePilot's business action planner.

Your task is to convert the user's request into a
structured e-commerce business action.

Currently ONLY one write action is supported:

update_product_price

Required fields:
- sku
- new_price

Important rules:

1. Never execute actions yourself.
2. Never claim that an action has already happened.
3. Only parse the user's requested operation.
4. If the user asks for an unsupported write action,
   return is_supported=false.
5. Only support ONE product per request for now.
6. Return JSON only.
7. Do not output markdown fences.

Supported JSON example:

{
  "is_supported": true,
  "action_type": "update_product_price",
  "sku": "SKU-0001",
  "new_price": 299,
  "rationale": "用户要求调整商品价格",
  "unsupported_reason": null
}

Unsupported example:

{
  "is_supported": false,
  "action_type": null,
  "sku": null,
  "new_price": null,
  "rationale": null,
  "unsupported_reason": "当前暂不支持该业务操作"
}
"""


@observe(
    name="action.plan"
)
def generate_action_plan(
    user_request: str,
) -> ActionPlan:

    client = get_llm_client()

    try:

        response = (
            client.chat.completions.create(
                model=get_model_name(),
                messages=[
                    {
                        "role": "system",
                        "content":
                            ACTION_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content":
                            user_request,
                    },
                ],
                response_format={
                    "type":
                        "json_object"
                },
                temperature=0,
                max_tokens=500,
            )
        )

    except Exception as exc:

        raise ActionPlanningError(
            f"Action planning failed: "
            f"{exc}"
        ) from exc


    content = (
        response
        .choices[0]
        .message
        .content
    )

    if not content:

        raise ActionPlanningError(
            "Action planner returned "
            "empty content."
        )


    try:

        data = json.loads(
            content
        )

        return (
            ActionPlan
            .model_validate(
                data
            )
        )

    except (
        json.JSONDecodeError,
        ValidationError,
    ) as exc:

        raise ActionPlanningError(
            "Invalid action plan: "
            f"{exc}"
        ) from exc