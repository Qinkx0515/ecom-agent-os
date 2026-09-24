import json
from uuid import uuid4

from ecom_agent_os.commerce_pilot.actions.builder import (
    build_action_graph,
)
from ecom_agent_os.commerce_pilot.workflow.persistence import (
    create_sqlite_checkpointer,
)


def main():

    request = input(
        "\n请输入业务操作：\n> "
    ).strip()

    if not request:

        request = (
            "把 SKU-0001 "
            "的价格调整为299元"
        )


    thread_id = (
        f"action-{uuid4()}"
    )


    config = {
        "configurable": {
            "thread_id":
                thread_id
        }
    }


    with create_sqlite_checkpointer() as saver:

        graph = build_action_graph(
            checkpointer=saver
        )


        result = graph.invoke(
            {
                "user_request":
                    request,
            },
            config=config,
            durability="sync",
            version="v2",
        )


        print(
            "\n===== Thread ID ====="
        )

        print(
            thread_id
        )


        if result.interrupts:

            interrupt_info = (
                result.interrupts[0]
            )

            print(
                "\n===== APPROVAL REQUIRED ====="
            )

            print(
                json.dumps(
                    interrupt_info.value,
                    ensure_ascii=False,
                    indent=2,
                )
            )

            print(
                "\nInterrupt ID:"
            )

            print(
                interrupt_info.id
            )

            print(
                "\nGraph 已暂停。"
            )

            print(
                "请保存上面的 thread_id。"
            )

            return


        print(
            "\n===== Result ====="
        )

        print(
            result.value
        )


if __name__ == "__main__":
    main()