from decimal import Decimal

from ecom_agent_os.commerce_pilot.evaluation.comparator import (
    results_equivalent,
)


def test_result_comparison_ignores_alias():

    actual = [{"total_sales": Decimal("100.00")}]

    expected = [{"gmv": Decimal("100.0")}]

    assert results_equivalent(
        actual,
        expected,
    )


def test_result_comparison_ignores_row_order():

    actual = [
        {
            "category": "耳机",
            "gmv": Decimal("100"),
        },
        {
            "category": "鼠标",
            "gmv": Decimal("200"),
        },
    ]

    expected = [
        {
            "name": "鼠标",
            "amount": Decimal("200"),
        },
        {
            "name": "耳机",
            "amount": Decimal("100"),
        },
    ]

    assert results_equivalent(
        actual,
        expected,
    )


def test_wrong_result_is_rejected():

    actual = [{"gmv": Decimal("99")}]

    expected = [{"gmv": Decimal("100")}]

    assert not results_equivalent(
        actual,
        expected,
    )
