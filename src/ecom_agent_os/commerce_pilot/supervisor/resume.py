from langgraph.types import (
    Command,
)

from ecom_agent_os.commerce_pilot.supervisor.builder import (
    build_supervisor_graph,
)
from ecom_agent_os.commerce_pilot.workflow.persistence import (
    create_sqlite_checkpointer,
)


def main():

    thread_id = input(
        "\n请输入 Supervisor thread_id：\n> "
    ).strip()


    if not thread_id:

        print(
            "thread_id 不能为空。"
        )

        return


    decision = input(
        "\n审批结果 "
        "(approve/reject)：\n> "
    ).strip().lower()


    if decision not in {
        "approve",
        "reject",
    }:

        print(
            "请输入 approve 或 reject。"
        )

        return


    comment = input(
        "\n审批备注：\n> "
    ).strip()


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
            Command(
                resume={
                    "decision":
                        decision,

                    "comment":
                        comment or None,
                }
            ),
            config=config,
            durability="sync",
            version="v2",
        )


        if result.interrupts:

            print(
                "\n仍有审批请求未处理。"
            )

            return


        state = result.value


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
            "\n===== Result ====="
        )

        print(
            state.get(
                "final_answer"
            )
        )


if __name__ == "__main__":
    main()