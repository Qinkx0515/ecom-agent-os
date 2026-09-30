from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph


class CommerceState(TypedDict, total=False):
    user_query: str
    intent: str
    plan: list[str]
    final_answer: str


def classify_intent(state: CommerceState) -> CommerceState:
    query = state["user_query"].lower()

    sales_keywords = [
        "gmv",
        "销售",
        "销量",
        "订单",
        "转化率",
        "退款率",
        "库存",
    ]

    if any(keyword in query for keyword in sales_keywords):
        intent = "sales_analysis"
    else:
        intent = "unsupported"

    return {
        "intent": intent,
    }


def build_sales_analysis_plan(
    state: CommerceState,
) -> CommerceState:
    plan = [
        "检查最近30天 GMV 与历史同期变化",
        "分析订单量和客单价变化",
        "分析流量和转化率变化",
        "检查退款率是否异常",
        "检查核心商品库存情况",
    ]

    return {
        "plan": plan,
        "final_answer": "已生成销售分析计划",
    }


def unsupported_request(state: CommerceState) -> CommerceState:
    return {"final_answer": ("当前 CommercePilot V0暂时只支持电商经营分析问题")}


def route_by_intent(state: CommerceState) -> Literal["sales_analysis", "unsupported"]:
    if state["intent"] == "sales_analysis":
        return "sales_analysis"

    return "unsupported"


def build_graph():
    builder = StateGraph(CommerceState)

    builder.add_node(
        "classify_intent",
        classify_intent,
    )
    builder.add_node(
        "sales_analysis",
        build_sales_analysis_plan,
    )
    builder.add_node(
        "unsupported",
        unsupported_request,
    )

    builder.add_edge(
        START,
        "classify_intent",
    )
    builder.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {"sales_analysis": "sales_analysis", "unsupported": "unsupported"},
    )
    builder.add_edge(
        "sales_analysis",
        END,
    )
    builder.add_edge("unsupported", END)

    graph = builder.compile()
    return graph
