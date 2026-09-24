import json
from uuid import uuid4

from ecom_agent_os.commerce_pilot.supervisor.builder import (
    build_supervisor_graph,
)
from ecom_agent_os.commerce_pilot.workflow.persistence import (
    create_sqlite_checkpointer,
)


def main():

    request = input(
        "\n请输入 CommercePilot 请求：\n> "
    ).strip()


    if not request:

        request = (
            "最近30天耳机品类"
            "GMV是多少？"
        )


    thread_id = (
        f"commerce-supervisor-"
        f"{uuid4()}"
    )


    config = {
        "configurable": {
            "thread_id":
                thread_id
        }
    }


    with create_sqlite_checkpointer() as saver:

        graph = (
            build_supervisor_graph(
                checkpointer=saver
            )
        )


        result = graph.invoke(
            {
                "request":
                    request
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

            print(
                "\n===== Human Approval Required ====="
            )

            for item in result.interrupts:

                print(
                    json.dumps(
                        item.value,
                        ensure_ascii=False,
                        indent=2,
                    )
                )

            print(
                "\nGraph 已暂停。"
            )

            return


        state = result.value


        print(
            "\n===== Route ====="
        )

        print(
            state.get(
                "route"
            )
        )


        print(
            "\n===== Confidence ====="
        )

        print(
            state.get(
                "route_confidence"
            )
        )


        print(
            "\n===== Route Reason ====="
        )

        print(
            state.get(
                "route_reason"
            )
        )


        print(
            "\n===== Agent Used ====="
        )

        print(
            state.get(
                "agent_used"
            )
        )


        print(
            "\n===== Final Answer ====="
        )

        print(
            state.get(
                "final_answer"
            )
        )


if __name__ == "__main__":
    main()