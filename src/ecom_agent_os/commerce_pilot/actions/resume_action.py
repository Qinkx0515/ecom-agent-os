from langgraph.types import (
    Command,
)

from ecom_agent_os.commerce_pilot.actions.builder import (
    build_action_graph,
)
from ecom_agent_os.commerce_pilot.workflow.persistence import (
    create_sqlite_checkpointer,
)


def main():

    thread_id = input("\n请输入 thread_id：\n> ").strip()

    if not thread_id:
        print("thread_id 不能为空。")

        return

    raw_decision = input("\n请输入审批结果 (approve/reject)：\n> ").strip().lower()

    if raw_decision not in {
        "approve",
        "reject",
    }:
        print("审批结果只能是 approve 或 reject。")

        return

    comment = input("\n审批备注（可为空）：\n> ").strip()

    config = {"configurable": {"thread_id": thread_id}}

    resume_value = {
        "decision": raw_decision,
        "comment": (comment if comment else None),
    }

    with create_sqlite_checkpointer() as saver:
        graph = build_action_graph(checkpointer=saver)

        result = graph.invoke(
            Command(resume=resume_value),
            config=config,
            durability="sync",
            version="v2",
        )

        if result.interrupts:
            print("\nGraph 仍在等待输入：")

            for item in result.interrupts:
                print(item.value)

            return

        state = result.value

        print("\n===== Final Status =====")

        print(state.get("status"))

        print("\n===== Result =====")

        print(state.get("action_result"))

        if state.get("error"):
            print("\n===== Error =====")

            print(state["error"])


if __name__ == "__main__":
    main()
