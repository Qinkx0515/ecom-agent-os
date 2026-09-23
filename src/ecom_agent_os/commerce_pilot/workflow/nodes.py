from ecom_agent_os.commerce_pilot.sql.executor import (
    SQLExecutionError,
    SQLExecutionResult,
)
from ecom_agent_os.commerce_pilot.sql.validator import (
    SQLValidationError,
)
from ecom_agent_os.commerce_pilot.text_to_sql.answer_generator import (
    AnswerGenerationError,
)
from ecom_agent_os.commerce_pilot.text_to_sql.generator import (
    LLMGenerationError,
)
from ecom_agent_os.commerce_pilot.workflow.dependencies import (
    CommerceDependencies,
)
from ecom_agent_os.commerce_pilot.workflow.state import (
    CommerceGraphState,
)

class CommerceNodes:

    def __init__(
        self,
        deps: CommerceDependencies,
    ):

        self.deps = deps


    def load_context(
        self,
        state: CommerceGraphState,
    ) -> CommerceGraphState:

        schema = (
            self.deps
            .schema_provider()
        )

        return {
            "schema": schema,
            "max_attempts": (
                state.get(
                    "max_attempts",
                    3,
                )
            ),
            "status":
                "context_loaded",
        }


    def generate_sql(
        self,
        state: CommerceGraphState,
    ) -> CommerceGraphState:

        attempt_number = (
            state.get(
                "attempt_number",
                0,
            )
            + 1
        )

        previous_sql = None

        if state.get(
            "last_error"
        ):

            previous_sql = (
                state.get(
                    "current_sql"
                )
            )

        try:

            generation = (
                self.deps.sql_generator(
                    question=state[
                        "question"
                    ],
                    schema=state[
                        "schema"
                    ],
                    previous_sql=(
                        previous_sql
                    ),
                    error_message=(
                        state.get(
                            "last_error"
                        )
                    ),
                )
            )

        except LLMGenerationError as exc:

            error = str(exc)

            return {
                "attempt_number":
                    attempt_number,

                "generation_ok":
                    False,

                "current_sql":
                    None,

                "last_error":
                    error,

                "status":
                    "generation_failed",

                "attempts": [
                    {
                        "attempt":
                            attempt_number,

                        "stage":
                            "generation",

                        "sql":
                            None,

                        "status":
                            "failed",

                        "error":
                            error,
                    }
                ],
            }

        if not generation.is_supported:

            return {
                "attempt_number":
                    attempt_number,

                "generation_ok":
                    True,

                "is_supported":
                    False,

                "unsupported_reason":
                    generation
                    .unsupported_reason,

                "query_plan":
                    generation.query_plan,

                "current_sql":
                    None,

                "last_error":
                    None,

                "status":
                    "unsupported",
            }

        return {
            "attempt_number":
                attempt_number,

            "generation_ok":
                True,

            "is_supported":
                True,

            "query_plan":
                generation.query_plan,

            "current_sql":
                generation.sql,

            "last_error":
                None,

            "status":
                "sql_generated",
        }


    def execute_sql(
        self,
        state: CommerceGraphState,
    ) -> CommerceGraphState:

        sql = state.get(
            "current_sql"
        )

        if not sql:

            error = (
                "No SQL is available "
                "for execution."
            )

            return {
                "execution_ok":
                    False,

                "last_error":
                    error,

                "status":
                    "execution_failed",

                "attempts": [
                    {
                        "attempt":
                            state[
                                "attempt_number"
                            ],

                        "stage":
                            "execution",

                        "sql":
                            None,

                        "status":
                            "failed",

                        "error":
                            error,
                    }
                ],
            }

        try:

            execution = (
                self.deps.sql_executor(
                    sql
                )
            )

        except (
            SQLValidationError,
            SQLExecutionError,
        ) as exc:

            error = str(exc)

            return {
                "execution_ok":
                    False,

                "last_error":
                    error[:1500],

                "status":
                    "execution_failed",

                "attempts": [
                    {
                        "attempt":
                            state[
                                "attempt_number"
                            ],

                        "stage":
                            "execution",

                        "sql":
                            sql,

                        "status":
                            "failed",

                        "error":
                            error[:1500],
                    }
                ],
            }

        return {
            "execution_ok":
                True,

            "columns":
                execution.columns,

            "rows":
                execution.rows,

            "truncated":
                execution.truncated,

            "current_sql":
                execution.sql,

            "last_error":
                None,

            "status":
                "execution_succeeded",

            "attempts": [
                {
                    "attempt":
                        state[
                            "attempt_number"
                        ],

                    "stage":
                        "execution",

                    "sql":
                        execution.sql,

                    "status":
                        "success",

                    "error":
                        None,
                }
            ],
        }

    def retry_or_fail(
        self,
        state: CommerceGraphState,
    ) -> CommerceGraphState:

        attempt = state.get(
            "attempt_number",
            0,
        )

        max_attempts = state.get(
            "max_attempts",
            3,
        )

        if attempt < max_attempts:

            return {
                "status":
                    "retrying",
            }

        return {
            "status":
                "max_attempts_reached",
        }


    def unsupported(
        self,
        state: CommerceGraphState,
    ) -> CommerceGraphState:

        reason = state.get(
            "unsupported_reason"
        )

        if not reason:

            reason = (
                "该问题无法通过当前"
                "电商分析数据库回答。"
            )

        return {
            "final_answer":
                f"该问题暂不支持："
                f"{reason}",

            "status":
                "unsupported",
        }


    def failed(
        self,
        state: CommerceGraphState,
    ) -> CommerceGraphState:

        attempt = state.get(
            "attempt_number",
            0,
        )

        error = state.get(
            "last_error"
        )

        return {
            "final_answer": (
                "Text-to-SQL 在 "
                f"{attempt} 次尝试后"
                "仍然失败。"

                f"\n最后错误："
                f"{error}"
            ),

            "status":
                "failed",
        }


    def generate_answer(
        self,
        state: CommerceGraphState,
    ) -> CommerceGraphState:

        result = SQLExecutionResult(
            columns=state.get(
                "columns",
                [],
            ),

            rows=state.get(
                "rows",
                [],
            ),

            row_count=len(
                state.get(
                    "rows",
                    [],
                )
            ),

            truncated=state.get(
                "truncated",
                False,
            ),

            sql=state.get(
                "current_sql",
                "",
            ),
        )

        try:

            answer = (
                self.deps.answer_generator(
                    question=state[
                        "question"
                    ],
                    result=result,
                )
            )

        except AnswerGenerationError as exc:

            return {
                "final_answer": (
                    "SQL 查询已经成功，"
                    "但自然语言总结失败。"

                    "\n你仍然可以查看"
                    "数据库返回结果。"
                ),

                "last_error":
                    str(exc),

                "status":
                    "partial_success",
            }

        return {
            "final_answer":
                answer,

            "status":
                "success",
        }