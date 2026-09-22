from ecom_agent_os.commerce_pilot.graph import build_graph


def main():

    graph = build_graph()

    result = graph.invoke(
        {
            "user_query":
                "帮我写一首秋天的诗词"
        }
    )

    print("\n===== CommercePilot =====")

    print(
        f"用户问题：{result['user_query']}"
    )

    print(
        f"识别意图：{result['intent']}"
    )

    print("\n分析计划：")

    for index, step in enumerate(
        result.get("plan", []),
        start=1,
    ):
        print(
            f"{index}. {step}"
        )

    print(
        f"\n系统结果："
        f"{result['final_answer']}"
    )


if __name__ == "__main__":
    main()