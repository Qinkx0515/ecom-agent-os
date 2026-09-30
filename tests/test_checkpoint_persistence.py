from langgraph.checkpoint.sqlite import (
    SqliteSaver,
)

from ecom_agent_os.commerce_pilot.sql.executor import (
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


def test_state_survives_checkpointer_reopen(
    tmp_path,
):

    checkpoint_file = tmp_path / "checkpoint.sqlite3"

    def fake_schema_provider():

        return "TABLE products(id)"

    def fake_generator(
        **kwargs,
    ):

        return SQLGeneration(
            is_supported=True,
            query_plan=["统计商品数量"],
            sql=("SELECT COUNT(*) AS product_count FROM products"),
            unsupported_reason=None,
        )

    def fake_executor(
        sql,
    ):

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

    config = {"configurable": {"thread_id": "checkpoint-test-thread"}}

    # ===== 第一个进程生命周期 =====

    with SqliteSaver.from_conn_string(str(checkpoint_file)) as saver:
        graph = build_commerce_graph(
            deps=deps,
            checkpointer=saver,
        )

        result = graph.invoke(
            {
                "question": "有多少商品？",
                "max_attempts": 3,
                "attempts": [],
            },
            config=config,
            durability="sync",
        )

        assert result["status"] == "success"

    # ===== 模拟程序关闭后重新打开 =====

    with SqliteSaver.from_conn_string(str(checkpoint_file)) as saver:
        graph = build_commerce_graph(
            deps=deps,
            checkpointer=saver,
        )

        snapshot = graph.get_state(config)

        assert snapshot.values["question"] == "有多少商品？"

        assert snapshot.values["status"] == "success"

        assert snapshot.values["final_answer"] == "当前共有100个商品。"

        assert snapshot.next == ()


def test_checkpoint_history_exists(
    tmp_path,
):

    checkpoint_file = tmp_path / "history.sqlite3"

    def fake_generator(
        **kwargs,
    ):

        return SQLGeneration(
            is_supported=True,
            query_plan=["统计商品"],
            sql=("SELECT COUNT(*) FROM products"),
            unsupported_reason=None,
        )

    deps = CommerceDependencies(
        schema_provider=lambda: "TABLE products(id)",
        sql_generator=(fake_generator),
        sql_executor=lambda sql: SQLExecutionResult(
            columns=["count"],
            rows=[{"count": 100}],
            row_count=1,
            truncated=False,
            sql=sql,
        ),
        answer_generator=(lambda question, result: "100个商品"),
    )

    config = {"configurable": {"thread_id": "history-thread"}}

    with SqliteSaver.from_conn_string(str(checkpoint_file)) as saver:
        graph = build_commerce_graph(
            deps=deps,
            checkpointer=saver,
        )

        graph.invoke(
            {
                "question": "有多少商品？",
                "max_attempts": 3,
                "attempts": [],
            },
            config=config,
            durability="sync",
        )

        history = list(graph.get_state_history(config))

        assert len(history) >= 4

        assert history[0].values["status"] == "success"
