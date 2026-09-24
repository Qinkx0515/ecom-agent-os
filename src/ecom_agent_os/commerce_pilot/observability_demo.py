from ecom_agent_os.commerce_pilot.service import (
    run_commercepilot_request,
)
from ecom_agent_os.observability.langfuse_client import (
    flush_langfuse,
)


def main():

    request = input(
        "\n请输入请求：\n> "
    ).strip()


    if not request:

        request = (
            "最近30天耳机品类"
            "GMV是多少？"
        )


    result = (
        run_commercepilot_request(
            request
        )
    )


    print(
        "\n===== Thread ====="
    )

    print(
        result[
            "thread_id"
        ]
    )


    if result[
        "interrupts"
    ]:

        print(
            "\n等待人工审批。"
        )

        for item in (
            result[
                "interrupts"
            ]
        ):

            print(
                item.value
            )

    else:

        state = result[
            "value"
        ]

        print(
            "\n===== Status ====="
        )

        print(
            state.get(
                "status"
            )
        )

        print(
            "\n===== Agent ====="
        )

        print(
            state.get(
                "agent_used"
            )
        )

        print(
            "\n===== Answer ====="
        )

        print(
            state.get(
                "final_answer"
            )
        )


    # CLI 是短生命周期进程，
    # 结束前主动 flush。

    flush_langfuse()


if __name__ == "__main__":
    main()