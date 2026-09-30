from ecom_agent_os.commerce_pilot.workflow.builder import (
    build_commerce_graph,
)


def main():

    print("\n============================")

    print("CommercePilot LangGraph V3")

    print("============================\n")

    question = input("请输入经营分析问题：\n> ").strip()

    if not question:
        question = "最近30天耳机品类GMV是多少？"

    graph = build_commerce_graph()

    result = graph.invoke(
        {
            "question": question,
            "max_attempts": 3,
            "attempts": [],
        }
    )

    print("\n===== Status =====")

    print(result.get("status"))

    print("\n===== Query Plan =====")

    for index, step in enumerate(
        result.get(
            "query_plan",
            [],
        ),
        start=1,
    ):
        print(f"{index}. {step}")

    print("\n===== SQL =====")

    print(result.get("current_sql"))

    print("\n===== Attempts =====")

    for attempt in result.get(
        "attempts",
        [],
    ):
        print(f"\nAttempt {attempt['attempt']}")

        print(f"Stage: {attempt['stage']}")

        print(f"Status: {attempt['status']}")

        if attempt["error"]:
            print(f"Error: {attempt['error']}")

    print("\n===== Rows =====")

    for row in result.get(
        "rows",
        [],
    ):
        print(row)

    print("\n===== Final Answer =====")

    print(result.get("final_answer"))


if __name__ == "__main__":
    main()
