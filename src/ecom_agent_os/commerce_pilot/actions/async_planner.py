import json

from langfuse import observe
from pydantic import ValidationError

from ecom_agent_os.commerce_pilot.actions.models import (
    ActionPlan,
)
from ecom_agent_os.commerce_pilot.actions.planner import (
    ACTION_SYSTEM_PROMPT,
    ActionPlanningError,
)
from ecom_agent_os.commerce_pilot.llm.async_client import (
    get_async_llm_client,
    get_async_model_name,
)


@observe(
    name="action.plan"
)
async def async_generate_action_plan(
    user_request: str,
) -> ActionPlan:

    client = (
        get_async_llm_client()
    )


    try:

        response = await (
            client
            .chat
            .completions
            .create(
                model=(
                    get_async_model_name()
                ),

                messages=[
                    {
                        "role":
                            "system",

                        "content":
                            ACTION_SYSTEM_PROMPT,
                    },
                    {
                        "role":
                            "user",

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
            "Action planning "
            f"failed: {exc}"
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

        return (
            ActionPlan
            .model_validate(
                json.loads(
                    content
                )
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