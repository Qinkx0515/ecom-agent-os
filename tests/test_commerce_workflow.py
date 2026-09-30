from ecom_agent_os.commerce_pilot.sql.executor import (
    SQLExecutionError,
    SQLExecutionResult,
)
from ecom_agent_os.commerce_pilot.text_to_sql.models import (
    SQLGeneration,
)
from ecom_agent_os.commerce_pilot.workflow.builder import (
    build_commerce_graph,
)
from ecom_agent_os.commerce_pilot.workflow.dependencies import (
    CommerceDependencies,
)


def test_graph_repairs_sql_after_failure():

    generator_calls = []

    def fake_schema_provider():

        return """
        TABLE: products

        COLUMNS:
        - id
        - name
        """

    def fake_generator(
        question,
        schema,
        previous_sql=None,
        error_message=None,
    ):

        generator_calls.append(
            {
                "previous_sql": previous_sql,
                "error_message": error_message,
            }
        )

        if len(generator_calls) == 1:
            return SQLGeneration(
                is_supported=True,
                query_plan=["第一次生成错误SQL"],
                sql=("SELECT bad_column FROM products"),
                unsupported_reason=None,
            )

        return SQLGeneration(
            is_supported=True,
            query_plan=["根据错误修复SQL"],
            sql=("SELECT COUNT(*) AS product_count FROM products"),
            unsupported_reason=None,
        )

    def fake_executor(
        sql,
    ):

        if "bad_column" in sql:
            raise SQLExecutionError('column "bad_column" does not exist')

        return SQLExecutionResult(
            columns=["product_count"],
            rows=[{"product_count": 100}],
            row_count=1,
            truncated=False,
            sql=sql,
        )

    def fake_answer_generator(
        question,
        result,
    ):

        return "当前共有100个商品。"

    deps = CommerceDependencies(
        schema_provider=(fake_schema_provider),
        sql_generator=(fake_generator),
        sql_executor=(fake_executor),
        answer_generator=(fake_answer_generator),
    )

    graph = build_commerce_graph(deps)

    result = graph.invoke(
        {
            "question": "有多少商品？",
            "max_attempts": 3,
            "attempts": [],
        }
    )

    assert result["status"] == "success"

    assert result["attempt_number"] == 2

    assert len(result["attempts"]) == 2

    assert result["attempts"][0]["status"] == "failed"

    assert result["attempts"][1]["status"] == "success"

    assert "bad_column" in generator_calls[1]["previous_sql"]

    assert "bad_column" in generator_calls[1]["error_message"]

    assert result["final_answer"] == "当前共有100个商品。"


def test_graph_rejects_unsupported_question():

    def fake_generator(
        **kwargs,
    ):

        return SQLGeneration(
            is_supported=False,
            query_plan=[],
            sql=None,
            unsupported_reason=("系统只支持只读分析。"),
        )

    deps = CommerceDependencies(
        schema_provider=lambda: "fake schema",
        sql_generator=(fake_generator),
        sql_executor=lambda sql: None,
        answer_generator=(lambda question, result: "should not run"),
    )

    graph = build_commerce_graph(deps)

    result = graph.invoke(
        {
            "question": "删除所有订单",
            "max_attempts": 3,
            "attempts": [],
        }
    )

    assert result["status"] == "unsupported"

    assert "只读" in result["final_answer"]

    def test_graph_stops_after_max_attempts():
        def fake_generator(
            **kwargs,
        ):
            return SQLGeneration(
                is_supported=True,
                query_plan=["生成SQL"],
                sql=("SELECT bad_column FROM products"),
                unsupported_reason=None,
            )

        def always_fail_executor(
            sql,
        ):
            raise SQLExecutionError('column "bad_column" does not exist')

        deps = CommerceDependencies(
            schema_provider=lambda: "fake schema",
            sql_generator=(fake_generator),
            sql_executor=(always_fail_executor),
            answer_generator=(lambda question, result: "should not run"),
        )

        graph = build_commerce_graph(deps)

        result = graph.invoke(
            {
                "question": "测试失败",
                "max_attempts": 2,
                "attempts": [],
            }
        )

        assert result["attempt_number"] == 2

        assert result["status"] == "failed"

        assert len(result["attempts"]) == 2
