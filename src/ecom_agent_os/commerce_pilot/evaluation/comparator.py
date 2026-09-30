import json
from datetime import (
    date,
    datetime,
)
from decimal import Decimal
from typing import Any


def normalize_scalar(
    value: Any,
) -> str:

    if value is None:
        return "<NULL>"

    if isinstance(
        value,
        Decimal,
    ):
        normalized = value.normalize()

        return str(normalized)

    if isinstance(
        value,
        float,
    ):
        return str(
            round(
                value,
                6,
            )
        )

    if isinstance(
        value,
        (date, datetime),
    ):
        return value.isoformat()

    return str(value)


def row_signature(
    row: dict[str, Any],
) -> str:

    values = [normalize_scalar(value) for value in row.values()]

    values.sort()

    return json.dumps(
        values,
        ensure_ascii=False,
    )


def canonicalize_rows(
    rows: list[dict[str, Any]],
) -> list[str]:

    signatures = [row_signature(row) for row in rows]

    return sorted(signatures)


def results_equivalent(
    actual_rows: list[dict],
    expected_rows: list[dict],
) -> bool:

    return canonicalize_rows(actual_rows) == canonicalize_rows(expected_rows)
