from commerce_pilot.sql.executor import (
    SQLExecutionError,
    execute_safe_sql,
)
from commerce_pilot.sql.validator import (
    SQLValidationError,
)


def main():

    # sql = """
    # SELECT
    #     p.category,
    #     ROUND(
    #         SUM(
    #             oi.quantity
    #             * oi.unit_price
    #         ),
    #         2
    #     ) AS gmv
    #
    # FROM order_items oi
    #
    # JOIN products p
    #     ON oi.product_id = p.id
    #
    # GROUP BY p.category
    #
    # ORDER BY gmv DESC
    # """

#     sql = """
# DELETE FROM orders
# """

    # sql = """
    #       SELECT *
    #       FROM users;
    #
    #       DROP TABLE orders; \
    #       """

    sql = """
          SELECT *
          FROM company_salary \
          """

    try:

        result = execute_safe_sql(
            sql
        )

        print(
            "\n===== SAFE SQL ====="
        )

        print(
            result.sql
        )

        print(
            "\n===== RESULT ====="
        )

        for row in result.rows:

            print(
                row
            )

        print(
            f"\nRows: "
            f"{result.row_count}"
        )

        print(
            f"Truncated: "
            f"{result.truncated}"
        )

    except SQLValidationError as exc:

        print(
            "SQL validation failed:"
        )

        print(
            exc
        )

    except SQLExecutionError as exc:

        print(
            "SQL execution failed:"
        )

        print(
            exc
        )


if __name__ == "__main__":
    main()