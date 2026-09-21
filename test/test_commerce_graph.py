from commerce_pilot.graph import build_graph


def test_sales_analysis_route():

    graph = build_graph()

    result = graph.invoke(
        {
            "user_query":
                "分析最近30天GMV下降原因"
        }
    )
    print(result)
    assert (
        result["intent"]
        == "sales_analysis"
    )

    assert len(
        result["plan"]
    ) > 0


def test_unsupported_route():

    graph = build_graph()

    result = graph.invoke(
        {
            "user_query":
                "帮我写一首诗"
        }
    )
    print(result)
    assert (
        result["intent"]
        == "unsupported"
    )
    print(result)

if __name__ == "__main__":
    test_sales_analysis_route()
    test_unsupported_route()