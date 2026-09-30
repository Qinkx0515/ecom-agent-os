from uuid import uuid4

from ecom_agent_os.commerce_pilot.workflow.builder import (
    build_commerce_graph,
)
from ecom_agent_os.commerce_pilot.workflow.persistence import (
    create_sqlite_checkpointer,
)


def main():

    question = input("\n请输入经营分析问题：\n> ").strip()

    if not question:
        question = "最近30天耳机品类GMV是多少？"

    thread_id = f"commerce-{uuid4()}"

    config = {"configurable": {"thread_id": thread_id}}

    print("\n===== Thread =====")

    print(thread_id)

    with create_sqlite_checkpointer() as checkpointer:
        graph = build_commerce_graph(checkpointer=checkpointer)

        result = graph.invoke(
            {
                "question": question,
                "max_attempts": 3,
                "attempts": [],
            },
            config=config,
            durability="sync",
        )

        print("\n===== Final Status =====")

        print(result.get("status"))

        print("\n===== Final Answer =====")

        print(result.get("final_answer"))


if __name__ == "__main__":
    main()
