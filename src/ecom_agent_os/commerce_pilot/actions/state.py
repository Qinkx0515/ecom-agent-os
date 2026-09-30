from typing import (
    Literal,
    TypedDict,
)


class ActionState(
    TypedDict,
    total=False,
):
    user_request: str

    action_id: str

    # ===== Plan =====

    plan_ok: bool

    is_supported: bool

    action_type: str | None

    sku: str | None

    new_price: str | None

    rationale: str | None

    unsupported_reason: str | None

    # ===== Product =====

    product_id: int

    product_name: str

    category: str

    old_price: str

    stock: int

    # ===== Risk =====

    price_change_pct: float

    risk_level: Literal[
        "low",
        "medium",
        "high",
    ]

    approval_required: bool

    # ===== Approval =====

    approval_decision: (
        Literal[
            "approve",
            "reject",
        ]
        | None
    )

    approval_comment: str | None

    # ===== Execution =====

    action_result: str | None

    error: str | None

    status: str
