from dataclasses import dataclass

import sqlglot
from langfuse import (
    get_client,
    observe,
)
from sqlglot import exp
from sqlglot.errors import ParseError

ALLOWED_TABLES = {
    "users",
    "products",
    "orders",
    "order_items",
    "traffic_daily",
    "refunds",
}


MAX_RESULT_ROWS = 200


@dataclass
class ValidationResult:
    sql: str

    tables: set[str]

    is_safe: bool


class SQLValidationError(ValueError):
    pass


def get_forbidden_expression_types():

    forbidden_names = [
        "Insert",
        "Update",
        "Delete",
        "Drop",
        "Create",
        "Alter",
        "Merge",
        "Command",
        "Transaction",
        "Commit",
        "Rollback",
        "Grant",
        "Revoke",
        "Copy",
    ]

    expression_types = []

    for name in forbidden_names:
        expression_type = getattr(
            exp,
            name,
            None,
        )

        if expression_type is not None:
            expression_types.append(expression_type)

    return tuple(expression_types)


FORBIDDEN_EXPRESSION_TYPES = get_forbidden_expression_types()


def parse_sql(
    sql: str,
):

    if not sql:
        raise SQLValidationError("SQL cannot be empty.")

    sql = sql.strip()

    try:
        statements = sqlglot.parse(
            sql,
            read="postgres",
        )

    except ParseError as exc:
        raise SQLValidationError(f"SQL parse failed: {exc}") from exc

    statements = [statement for statement in statements if statement is not None]

    if len(statements) != 1:
        raise SQLValidationError("Only one SQL statement is allowed.")

    return statements[0]


def validate_read_only(
    tree,
) -> None:

    for node in tree.walk():
        if isinstance(
            node,
            FORBIDDEN_EXPRESSION_TYPES,
        ):
            raise SQLValidationError(
                "Only read-only SQL "
                "is allowed. "
                f"Forbidden operation: "
                f"{type(node).__name__}"
            )


def validate_query_type(
    tree,
) -> None:

    allowed_root_types = tuple(
        expression_type
        for expression_type in [
            getattr(
                exp,
                "Select",
                None,
            ),
            getattr(
                exp,
                "Union",
                None,
            ),
            getattr(
                exp,
                "Intersect",
                None,
            ),
            getattr(
                exp,
                "Except",
                None,
            ),
        ]
        if expression_type is not None
    )

    if not isinstance(
        tree,
        allowed_root_types,
    ):
        raise SQLValidationError("SQL must be a SELECT-style query.")


def extract_tables(
    tree,
) -> set[str]:

    cte_names = extract_cte_names(tree)

    tables = {
        table.name for table in tree.find_all(exp.Table) if table.name not in cte_names
    }

    return tables


def validate_tables(
    tables: set[str],
) -> None:

    unknown_tables = tables - ALLOWED_TABLES

    if unknown_tables:
        raise SQLValidationError(
            "Query accesses "
            "non-whitelisted tables: " + ", ".join(sorted(unknown_tables))
        )


def extract_cte_names(
    tree,
) -> set[str]:

    cte_names = set()

    for cte in tree.find_all(exp.CTE):
        if cte.alias:
            cte_names.add(cte.alias)

    return cte_names


@observe(
    name="sql.validate",
    capture_input=False,
)
def validate_sql(
    sql: str,
) -> ValidationResult:

    tree = parse_sql(sql)

    validate_read_only(tree)

    validate_query_type(tree)

    tables = extract_tables(tree)

    langfuse = get_client()

    langfuse.update_current_span(
        metadata={
            "tables": sorted(tables),
            "statement_count": 1,
            "read_only": True,
        }
    )

    if not tables:
        raise SQLValidationError(
            "Query must access at least one allowed business table."
        )

    validate_tables(tables)

    normalized_sql = tree.sql(
        dialect="postgres",
        pretty=True,
    )

    return ValidationResult(
        sql=normalized_sql,
        tables=tables,
        is_safe=True,
    )


if __name__ == "__main__":
    examples = [
        """
        SELECT
            category,
            COUNT(*)
        FROM products
        GROUP BY category
        """,
        """
        DELETE
        FROM orders
        """,
        """
        SELECT *
        FROM secret_table
        """,
        """
        SELECT *
        FROM products;

        DROP TABLE orders;
        """,
    ]

    for sql in examples:
        print("\n======================")

        print(sql.strip())

        try:
            result = validate_sql(sql)

            print("\nSAFE:")

            print(result.sql)

        except SQLValidationError as exc:
            print("\nBLOCKED:")

            print(exc)
