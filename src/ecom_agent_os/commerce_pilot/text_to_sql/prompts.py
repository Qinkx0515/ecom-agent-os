from ecom_agent_os.commerce_pilot.text_to_sql.business_semantics import (
    BUSINESS_SEMANTICS,
)


SQL_SYSTEM_PROMPT = """
You are CommercePilot's Text-to-SQL agent.

Your job is to convert READ-ONLY e-commerce analytics
questions into PostgreSQL queries.

You are NOT allowed to create SQL that modifies data.

Allowed query type:
- SELECT
- WITH ... SELECT

Forbidden:
- INSERT
- UPDATE
- DELETE
- DROP
- ALTER
- CREATE
- TRUNCATE
- GRANT
- REVOKE
- COPY

Rules:

1. Only use tables and columns from the provided schema.

2. Follow the provided business metric definitions exactly.

3. Use explicit JOIN conditions.

4. Avoid SELECT * unless absolutely necessary.

5. Do not invent tables or columns.

6. If the request asks to modify data or cannot be answered
   using the provided database, set is_supported=false.

7. Return ONLY a valid JSON object.

8. Do not output markdown code fences.

Required JSON format:

{
  "is_supported": true,
  "query_plan": [
    "short step 1",
    "short step 2"
  ],
  "sql": "SELECT ...",
  "unsupported_reason": null
}

Unsupported example:

{
  "is_supported": false,
  "query_plan": [],
  "sql": null,
  "unsupported_reason": "reason"
}
"""


def build_sql_prompt(
    question: str,
    schema: str,
    previous_sql: str | None = None,
    error_message: str | None = None,
) -> str:

    parts = [
        "DATABASE SCHEMA:",
        schema,
        "",
        "BUSINESS SEMANTICS:",
        BUSINESS_SEMANTICS,
        "",
        "USER QUESTION:",
        question,
    ]

    if previous_sql:

        parts.extend(
            [
                "",
                "PREVIOUS SQL THAT FAILED:",
                previous_sql,
            ]
        )

    if error_message:

        parts.extend(
            [
                "",
                "ERROR FROM THE PREVIOUS ATTEMPT:",
                error_message,
                "",
                "Repair the SQL based on this error.",
                "Do not blindly repeat the same SQL.",
            ]
        )

    parts.extend(
        [
            "",
            "Return the result as JSON only.",
        ]
    )

    return "\n".join(parts)