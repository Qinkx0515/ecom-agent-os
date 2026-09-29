import os

from dotenv import load_dotenv
from langfuse.openai import (
    AsyncOpenAI,
)


load_dotenv()


_async_client: (
    AsyncOpenAI
    | None
) = None


def get_async_llm_client(
) -> AsyncOpenAI:

    global _async_client

    if _async_client is None:

        api_key = os.getenv(
            "DEEPSEEK_API_KEY"
        )

        base_url = os.getenv(
            "DEEPSEEK_BASE_URL",
            "https://api.deepseek.com",
        )

        if not api_key:

            raise RuntimeError(
                "DEEPSEEK_API_KEY "
                "is not configured."
            )

        _async_client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    return _async_client


def get_async_model_name(
) -> str:

    return os.getenv(
        "DEEPSEEK_MODEL",
        "deepseek-flash",
    )


async def close_async_llm_client():

    global _async_client

    if _async_client is None:
        return

    await _async_client.close()

    _async_client = None