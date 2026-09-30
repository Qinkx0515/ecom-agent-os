from ecom_agent_os.commerce_pilot.sql.executor import (
    SQLExecutionError,
    SQLExecutionResult,
)
from ecom_agent_os.commerce_pilot.text_to_sql.models import (
    SQLGeneration,
)
from ecom_agent_os.commerce_pilot.workflow.async_builder import (
    build_async_commerce_graph,
)
from ecom_agent_os.commerce_pilot.workflow.async_dependencies import (
    AsyncCommerceDependencies,
)


async def test_async_graph_repairs_sql():

    calls = []

    async def fake_schema():

        return "TABLE products(id)"

    async def fake_generator(
        question,
        schema,
        previous_sql=None,
        error_message=None,
    ):

        calls.append(
            {
                "previous_sql": previous_sql,
                "error_message": error_message,
            }
        )

        if len(calls) == 1:
            return SQLGeneration(
                is_supported=True,
                query_plan=["生成错误SQL"],
                sql=("SELECT bad_column FROM products"),
                unsupported_reason=None,
            )

        return SQLGeneration(
            is_supported=True,
            query_plan=["修复SQL"],
            sql=("SELECT COUNT(*) AS product_count FROM products"),
            unsupported_reason=None,
        )

    async def fake_executor(
        sql,
    ):

        if "bad_column" in sql:
            raise SQLExecutionError("bad_column does not exist")

        return SQLExecutionResult(
            columns=["product_count"],
            rows=[{"product_count": 100}],
            row_count=1,
            truncated=False,
            sql=sql,
        )

    async def fake_answer(
        question,
        result,
    ):

        return "当前共有100个商品。"

    deps = AsyncCommerceDependencies(
        schema_provider=(fake_schema),
        sql_generator=(fake_generator),
        sql_executor=(fake_executor),
        answer_generator=(fake_answer),
    )

    graph = build_async_commerce_graph(deps)

    result = await graph.ainvoke(
        {
            "question": "有多少商品？",
            "max_attempts": 3,
            "attempts": [],
        }
    )

    assert result["status"] == "success"

    assert result["attempt_number"] == 2

    assert len(calls) == 2

    assert "bad_column" in calls[1]["error_message"]
