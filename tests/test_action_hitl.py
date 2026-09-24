from decimal import Decimal

from langgraph.checkpoint.sqlite import (
    SqliteSaver,
)
from langgraph.types import (
    Command,
)

from ecom_agent_os.commerce_pilot.actions.builder import (
    build_action_graph,
)
from ecom_agent_os.commerce_pilot.actions.dependencies import (
    ActionDependencies,
)
from ecom_agent_os.commerce_pilot.actions.models import (
    ActionPlan,
)
from ecom_agent_os.commerce_pilot.actions.repository import (
    PriceUpdateResult,
    ProductSnapshot,
)


def test_action_requires_approval_and_can_resume(
    tmp_path,
):

    checkpoint_file = (
        tmp_path
        / "hitl.sqlite3"
    )


    update_calls = []


    def fake_planner(
        request,
    ):

        return ActionPlan(
            is_supported=True,
            action_type=(
                "update_product_price"
            ),
            sku="SKU-0001",
            new_price=Decimal(
                "299"
            ),
            rationale="test",
            unsupported_reason=None,
        )


    def fake_product_reader(
        sku,
    ):

        return ProductSnapshot(
            id=1,
            sku=sku,
            name="测试耳机",
            category="耳机",
            price=Decimal(
                "399"
            ),
            stock=100,
        )


    def fake_price_updater(
        sku,
        new_price,
        expected_old_price,
    ):

        update_calls.append(
            {
                "sku":
                    sku,

                "new_price":
                    new_price,

                "expected_old_price":
                    expected_old_price,
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


    deps = ActionDependencies(
        action_planner=(
            fake_planner
        ),

        product_reader=(
            fake_product_reader
        ),

        price_updater=(
            fake_price_updater
        ),
    )


    config = {
        "configurable": {
            "thread_id":
                "hitl-test"
        }
    }


    # ===== Process Lifecycle 1 =====

    with SqliteSaver.from_conn_string(
        str(
            checkpoint_file
        )
    ) as saver:

        graph = build_action_graph(
            deps=deps,
            checkpointer=saver,
        )


        first = graph.invoke(
            {
                "user_request":
                    (
                        "把SKU-0001"
                        "价格改为299"
                    )
            },
            config=config,
            durability="sync",
            version="v2",
        )


        assert len(
            first.interrupts
        ) == 1


        # 还没审批
        # 数据库写操作绝对不能发生

        assert (
            update_calls
            == []
        )


    # ===== Process Lifecycle 2 =====

    with SqliteSaver.from_conn_string(
        str(
            checkpoint_file
        )
    ) as saver:

        graph = build_action_graph(
            deps=deps,
            checkpointer=saver,
        )


        resumed = graph.invoke(
            Command(
                resume={
                    "decision":
                        "approve",

                    "comment":
                        "test approval",
                }
            ),
            config=config,
            durability="sync",
            version="v2",
        )


        assert (
            resumed.value[
                "status"
            ]
            == "success"
        )


        assert len(
            update_calls
        ) == 1


        assert (
            update_calls[0][
                "new_price"
            ]
            == Decimal(
                "299"
            )
        )



def test_rejected_action_is_not_executed(
    tmp_path,
):

    checkpoint_file = (
        tmp_path
        / "reject.sqlite3"
    )


    update_calls = []


    deps = ActionDependencies(

        action_planner=lambda request:
            ActionPlan(
                is_supported=True,
                action_type=(
                    "update_product_price"
                ),
                sku="SKU-0002",
                new_price=Decimal(
                    "199"
                ),
                rationale="test",
                unsupported_reason=None,
            ),


        product_reader=lambda sku:
            ProductSnapshot(
                id=2,
                sku=sku,
                name="测试商品",
                category="耳机",
                price=Decimal(
                    "299"
                ),
                stock=50,
            ),


        price_updater=lambda **kwargs:
            update_calls.append(
                kwargs
            ),
    )


    config = {
        "configurable": {
            "thread_id":
                "reject-test"
        }
    }


    with SqliteSaver.from_conn_string(
        str(
            checkpoint_file
        )
    ) as saver:

        graph = build_action_graph(
            deps=deps,
            checkpointer=saver,
        )

        first = graph.invoke(
            {
                "user_request":
                    "修改价格"
            },
            config=config,
            version="v2",
        )

        assert (
            len(
                first.interrupts
            )
            == 1
        )


    with SqliteSaver.from_conn_string(
        str(
            checkpoint_file
        )
    ) as saver:

        graph = build_action_graph(
            deps=deps,
            checkpointer=saver,
        )

        resumed = graph.invoke(
            Command(
                resume={
                    "decision":
                        "reject",
                    "comment":
                        "不批准",
                }
            ),
            config=config,
            version="v2",
        )


        assert (
            resumed.value[
                "status"
            ]
            == "rejected"
        )

        assert (
            update_calls
            == []
        )