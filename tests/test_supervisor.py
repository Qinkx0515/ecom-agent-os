from decimal import Decimal

from ecom_agent_os.commerce_pilot.actions.dependencies import (
    ActionDependencies,
)
from ecom_agent_os.commerce_pilot.actions.models import (
    ActionPlan,
)
from ecom_agent_os.commerce_pilot.actions.repository import (
    ProductSnapshot,
)
from ecom_agent_os.commerce_pilot.sql.executor import (
    SQLExecutionResult,
)
from ecom_agent_os.commerce_pilot.supervisor.builder import (
    build_supervisor_graph,
)
from ecom_agent_os.commerce_pilot.supervisor.dependencies import (
    SupervisorDependencies,
)
from ecom_agent_os.commerce_pilot.supervisor.models import (
    SupervisorDecision,
)
from ecom_agent_os.commerce_pilot.text_to_sql.models import (
    SQLGeneration,
)
from ecom_agent_os.commerce_pilot.workflow.dependencies import (
    CommerceDependencies,
)


def test_supervisor_routes_to_analytics():

    analytics_deps = CommerceDependencies(

        schema_provider=lambda:
            "TABLE products(id)",

        sql_generator=lambda **kwargs:
            SQLGeneration(
                is_supported=True,
                query_plan=[
                    "统计商品数量"
                ],
                sql=(
                    "SELECT COUNT(*) "
                    "AS product_count "
                    "FROM products"
                ),
                unsupported_reason=None,
            ),

        sql_executor=lambda sql:
            SQLExecutionResult(
                columns=[
                    "product_count"
                ],
                rows=[
                    {
                        "product_count":
                            100
                    }
                ],
                row_count=1,
                truncated=False,
                sql=sql,
            ),

        answer_generator=(
            lambda question, result:
                "当前共有100个商品。"
        ),
    )


    deps = SupervisorDependencies(

        request_router=lambda request:
            SupervisorDecision(
                route="analytics",
                confidence=0.99,
                reason="数据查询",
            ),

        analytics_deps=(
            analytics_deps
        ),
    )


    graph = (
        build_supervisor_graph(
            deps=deps
        )
    )


    result = graph.invoke(
        {
            "request":
                "有多少商品？"
        }
    )


    assert (
        result[
            "agent_used"
        ]
        == "analytics"
    )


    assert (
        result[
            "final_answer"
        ]
        == "当前共有100个商品。"
    )


    assert (
        result[
            "status"
        ]
        == "success"
    )



from langgraph.checkpoint.sqlite import (
    SqliteSaver,
)
from langgraph.types import (
    Command,
)

from ecom_agent_os.commerce_pilot.actions.repository import (
    PriceUpdateResult,
)


def test_supervisor_action_hitl(
    tmp_path,
):

    updates = []


    action_deps = ActionDependencies(

        action_planner=lambda request:
            ActionPlan(
                is_supported=True,
                action_type=(
                    "update_product_price"
                ),
                sku="SKU-TEST",
                new_price=Decimal(
                    "299"
                ),
                rationale="test",
                unsupported_reason=None,
            ),

        product_reader=lambda sku:
            ProductSnapshot(
                id=1,
                sku=sku,
                name="测试耳机",
                category="耳机",
                price=Decimal(
                    "399"
                ),
                stock=100,
            ),

        price_updater=lambda sku,new_price,expected_old_price: None,
    )

    def fake_updater(
        sku,
        new_price,
        expected_old_price,
    ):

        updates.append(
            {
                "sku": sku,
                "new_price": new_price,
            }
        )

        return PriceUpdateResult(
            sku=sku,
            old_price=(
                expected_old_price
            ),
            new_price=(
                new_price
            ),
            status="updated",
        )


    action_deps = ActionDependencies(

        action_planner=lambda request:
            ActionPlan(
                is_supported=True,
                action_type=(
                    "update_product_price"
                ),
                sku="SKU-TEST",
                new_price=Decimal(
                    "299"
                ),
                rationale="test",
                unsupported_reason=None,
            ),

        product_reader=lambda sku:
            ProductSnapshot(
                id=1,
                sku=sku,
                name="测试耳机",
                category="耳机",
                price=Decimal(
                    "399"
                ),
                stock=100,
            ),

        price_updater=(
            fake_updater
        ),
    )


    deps = SupervisorDependencies(

        request_router=lambda request:
            SupervisorDecision(
                route="action",
                confidence=0.99,
                reason="写操作",
            ),

        action_deps=(
            action_deps
        ),
    )


    checkpoint_path = (
        tmp_path
        / "supervisor.sqlite3"
    )


    config = {
        "configurable": {
            "thread_id":
                "supervisor-hitl"
        }
    }


    with SqliteSaver.from_conn_string(
        str(
            checkpoint_path
        )
    ) as saver:

        graph = (
            build_supervisor_graph(
                deps=deps,
                checkpointer=saver,
            )
        )


        first = graph.invoke(
            {
                "request":
                    (
                        "把商品价格"
                        "调整到299"
                    )
            },
            config=config,
            version="v2",
        )


        assert len(
            first.interrupts
        ) == 1


        assert (
            updates
            == []
        )


    with SqliteSaver.from_conn_string(
        str(
            checkpoint_path
        )
    ) as saver:

        graph = (
            build_supervisor_graph(
                deps=deps,
                checkpointer=saver,
            )
        )


        resumed = graph.invoke(
            Command(
                resume={
                    "decision":
                        "approve",

                    "comment":
                        "approved",
                }
            ),
            config=config,
            version="v2",
        )


        assert (
            resumed.value[
                "agent_used"
            ]
            == "action"
        )


        assert (
            len(
                updates
            )
            == 1
        )