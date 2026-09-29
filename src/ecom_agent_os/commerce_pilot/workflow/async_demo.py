import asyncio

from ecom_agent_os.commerce_pilot.workflow.async_builder import (
    build_async_commerce_graph,
)


async def main():

    graph = (
        build_async_commerce_graph()
    )


    result = await graph.ainvoke(
        {
            "question":
                "最近30天耳机品类"
                "GMV是多少？",

            "max_attempts":
                3,

            "attempts":
                [],
        }
    )


    print(
        result[
            "status"
        ]
    )

    print(
        result[
            "current_sql"
        ]
    )

    print(
        result[
            "final_answer"
        ]
    )


if __name__ == "__main__":

    asyncio.run(
        main()
    )