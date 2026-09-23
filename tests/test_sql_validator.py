import pytest

from ecom_agent_os.commerce_pilot.sql.validator import (
    SQLValidationError,
    validate_sql,
)


def test_valid_select():

    result = validate_sql(
        """
        SELECT
            category,
            COUNT(*)
        FROM products
        GROUP BY category
        """
    )

    assert result.is_safe

    assert (
        "products"
        in result.tables
    )


def test_delete_is_blocked():

    with pytest.raises(
        SQLValidationError
    ):

        validate_sql(
            "DELETE FROM orders"
        )


def test_drop_is_blocked():

    with pytest.raises(
        SQLValidationError
    ):

        validate_sql(
            "DROP TABLE products"
        )


def test_multiple_statements_blocked():

    with pytest.raises(
        SQLValidationError
    ):

        validate_sql(
            """
            SELECT *
            FROM products;

            DROP TABLE orders;
            """
        )


def test_unknown_table_blocked():

    with pytest.raises(
        SQLValidationError
    ):

        validate_sql(
            """
            SELECT *
            FROM secret_table
            """
        )


def test_cte_is_allowed():

    result = validate_sql(
        """
        WITH recent_orders AS (
            SELECT *
            FROM orders
        )

        SELECT *
        FROM recent_orders
        """
    )

    assert result.is_safe

    assert (
        result.tables
        == {"orders"}
    )