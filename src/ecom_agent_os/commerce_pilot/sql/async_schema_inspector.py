from sqlalchemy import inspect

from ecom_agent_os.database.async_session import (
    async_engine,
)
from ecom_agent_os.commerce_pilot.sql.schema_inspector import (
    ALLOWED_TABLES,
)


def _inspect_schema(
    sync_connection,
) -> dict[str, dict]:

    inspector = inspect(
        sync_connection
    )

    database_tables = set(
        inspector.get_table_names()
    )

    schema: dict[str, dict] = {}

    for table_name in sorted(
        ALLOWED_TABLES
    ):

        if (
            table_name
            not in database_tables
        ):
            continue

        columns = (
            inspector.get_columns(
                table_name
            )
        )

        foreign_keys = (
            inspector.get_foreign_keys(
                table_name
            )
        )

        schema[table_name] = {

            "columns": [
                {
                    "name":
                        column["name"],

                    "type":
                        str(
                            column["type"]
                        ),

                    "nullable":
                        column[
                            "nullable"
                        ],
                }
                for column
                in columns
            ],

            "foreign_keys": [
                {
                    "columns":
                        fk[
                            "constrained_columns"
                        ],

                    "target_table":
                        fk[
                            "referred_table"
                        ],

                    "target_columns":
                        fk[
                            "referred_columns"
                        ],
                }
                for fk
                in foreign_keys
            ],
        }

    return schema

async def async_get_schema_dict(
) -> dict[str, dict]:

    async with (
        async_engine.connect()
    ) as connection:

        schema = await (
            connection.run_sync(
                _inspect_schema
            )
        )

    return schema

async def async_format_schema_for_llm(
) -> str:

    schema = await (
        async_get_schema_dict()
    )

    lines: list[str] = []

    for (
        table_name,
        info,
    ) in schema.items():

        lines.append(
            f"TABLE: {table_name}"
        )

        lines.append(
            "COLUMNS:"
        )

        for column in (
            info["columns"]
        ):

            lines.append(
                f"  - "
                f"{column['name']} "
                f"({column['type']})"
            )

        if info[
            "foreign_keys"
        ]:

            lines.append(
                "FOREIGN KEYS:"
            )

            for fk in (
                info[
                    "foreign_keys"
                ]
            ):

                source = ", ".join(
                    fk["columns"]
                )

                target = ", ".join(
                    fk[
                        "target_columns"
                    ]
                )

                lines.append(
                    f"  - "
                    f"{source} -> "
                    f"{fk['target_table']}."
                    f"{target}"
                )

        lines.append("")

    return "\n".join(
        lines
    )