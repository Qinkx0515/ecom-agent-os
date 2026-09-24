from decimal import Decimal
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


class ActionPlan(BaseModel):

    is_supported: bool

    action_type: (
        Literal["update_product_price"]
        | None
    ) = None

    sku: str | None = None

    new_price: Decimal | None = Field(
        default=None,
        gt=0,
    )

    rationale: str | None = None

    unsupported_reason: str | None = None


    @model_validator(
        mode="after"
    )
    def validate_action(
        self,
    ):

        if self.is_supported:

            if (
                self.action_type
                is None
            ):
                raise ValueError(
                    "action_type is required."
                )

            if not self.sku:
                raise ValueError(
                    "sku is required."
                )

            if self.new_price is None:
                raise ValueError(
                    "new_price is required."
                )

        else:

            if (
                not self
                .unsupported_reason
            ):
                raise ValueError(
                    "unsupported_reason "
                    "is required."
                )

        return self


class ApprovalDecision(
    BaseModel
):

    decision: Literal[
        "approve",
        "reject",
    ]

    comment: str | None = None