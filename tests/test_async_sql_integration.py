import pytest

from ecom_agent_os.commerce_pilot.sql.async_executor import (
    async_execute_safe_sql,
)


@pytest.mark.integration
async def test_async_sql_executor():

    result = await async_execute_safe_sql(
        """
            SELECT
                COUNT(*) AS product_count
            FROM products
            """
    )

    assert result.row_count == 1

    assert result.rows[0]["product_count"] > 0
