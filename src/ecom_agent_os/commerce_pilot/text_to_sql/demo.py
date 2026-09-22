from ecom_agent_os.commerce_pilot.text_to_sql.service import (
    TextToSQLFailed,
    UnsupportedQuestionError,
    run_text_to_sql,
)


def main():

    print(
        "\n=========================="
    )

    print(
        "CommercePilot Text-to-SQL"
    )

    print(
        "==========================\n"
    )

    question = input(
        "请输入经营分析问题：\n> "
    ).strip()

    if not question:

        question = (
            "最近30天耳机品类GMV是多少？"
        )

    try:

        result = run_text_to_sql(
            question
        )

    except UnsupportedQuestionError as exc:

        print(
            "\n该问题暂不支持："
        )

        print(
            exc
        )

        return

    except TextToSQLFailed as exc:

        print(
            "\nText-to-SQL失败："
        )

        print(
            exc
        )

        return

    print(
        "\n===== Query Plan ====="
    )

    for index, step in enumerate(
        result.query_plan,
        start=1,
    ):

        print(
            f"{index}. {step}"
        )

    print(
        "\n===== SQL ====="
    )

    print(
        result.sql
    )

    print(
        "\n===== Database Result ====="
    )

    for row in result.rows:

        print(
            row
        )

    print(
        "\n===== Attempts ====="
    )

    for attempt in result.attempts:

        status = (
            "FAILED"
            if attempt.error
            else "SUCCESS"
        )

        print(
            f"Attempt "
            f"{attempt.attempt}: "
            f"{status}"
        )

        if attempt.error:

            print(
                f"  Error: "
                f"{attempt.error}"
            )

    print(
        "\n===== Final Answer ====="
    )

    print(
        result.answer
    )


if __name__ == "__main__":
    main()