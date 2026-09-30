import pytest

from ecom_agent_os.commerce_pilot.sql.executor import (
    execute_safe_sql,
)

pytestmark = pytest.mark.integration


def test_execute_product_count():

    result = execute_safe_sql(
        """
        SELECT
            COUNT(*) AS product_count
        FROM products
        """
    )

    assert result.row_count == 1

    assert result.rows[0]["product_count"] > 0


def test_execute_category_query():

    result = execute_safe_sql(
        """
        SELECT
            category,
            COUNT(*) AS count
        FROM products
        GROUP BY category
        """
    )

    assert result.row_count > 0

    categories = {row["category"] for row in result.rows}

    assert "耳机" in categories
