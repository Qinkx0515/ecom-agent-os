from ecom_agent_os.commerce_pilot.sql.executor import (
    SQLExecutionError,
    SQLExecutionResult,
)
from ecom_agent_os.commerce_pilot.text_to_sql.models import (
    SQLGeneration,
)
from ecom_agent_os.commerce_pilot.text_to_sql.service import (
    run_text_to_sql,
)


def test_sql_retry_after_execution_error():

    call_count = 0

    received_errors = []

    def fake_generator(
        question,
        schema,
        previous_sql=None,
        error_message=None,
    ):

        nonlocal call_count

        call_count += 1

        received_errors.append(
            error_message
        )

        if call_count == 1:

            return SQLGeneration(
                is_supported=True,
                query_plan=[
                    "第一次生成错误SQL"
                ],
                sql=(
                    "SELECT bad_column "
                    "FROM products"
                ),
                unsupported_reason=None,
            )

        return SQLGeneration(
            is_supported=True,
            query_plan=[
                "根据数据库错误修复SQL"
            ],
            sql=(
                "SELECT COUNT(*) "
                "AS product_count "
                "FROM products"
            ),
            unsupported_reason=None,
        )

    def fake_executor(
        sql,
    ):

        if "bad_column" in sql:

            raise SQLExecutionError(
                'column "bad_column" '
                "does not exist"
            )

        return SQLExecutionResult(
            columns=[
                "product_count"
            ],
            rows=[
                {
                    "product_count": 100
                }
            ],
            row_count=1,
            truncated=False,
            sql=sql,
        )

    def fake_answer_generator(
        question,
        result,
    ):

        return "当前共有100个商品。"

    result = run_text_to_sql(
        question="数据库里有多少商品？",
        sql_generator=fake_generator,
        sql_executor=fake_executor,
        answer_generator=(
            fake_answer_generator
        ),
    )

    assert call_count == 2

    assert len(
        result.attempts
    ) == 2

    assert (
        result.attempts[0].error
        is not None
    )

    assert (
        result.attempts[1].error
        is None
    )

    assert (
        "bad_column"
        in received_errors[1]
    )

    assert (
        result.answer
        == "当前共有100个商品。"
    )