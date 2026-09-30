from ecom_agent_os.commerce_pilot.workflow.builder import (
    build_commerce_graph,
)
from ecom_agent_os.commerce_pilot.workflow.persistence import (
    create_sqlite_checkpointer,
)


def main():

    thread_id = input("请输入 thread_id：\n> ").strip()

    if not thread_id:
        print("thread_id 不能为空。")

        return

    config = {"configurable": {"thread_id": thread_id}}

    with create_sqlite_checkpointer() as checkpointer:
        graph = build_commerce_graph(checkpointer=checkpointer)

        snapshot = graph.get_state(config)

        history = list(graph.get_state_history(config))

        print("\n===== Checkpoint History =====")

        for index, state in enumerate(
            history,
            start=1,
        ):
            print(f"\n--- Snapshot {index} ---")

            print("Checkpoint ID:")

            print(state.config["configurable"].get("checkpoint_id"))

            print("Next:")

            print(state.next)

            print("Status:")

            print(state.values.get("status"))

            print("Attempt:")

            print(state.values.get("attempt_number"))

        print("\n===== State Snapshot =====")

        print("Values:")

        print(snapshot.values)

        print("\nNext:")

        print(snapshot.next)

        print("\nConfig:")

        print(snapshot.config)

        print("\nMetadata:")

        print(snapshot.metadata)


if __name__ == "__main__":
    main()
