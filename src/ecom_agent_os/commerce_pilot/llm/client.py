import os
from functools import lru_cache

from dotenv import load_dotenv
from langfuse.openai import OpenAI

load_dotenv()


@lru_cache(maxsize=1)
def get_llm_client() -> OpenAI:

    api_key = os.getenv("DEEPSEEK_API_KEY")

    base_url = os.getenv(
        "DEEPSEEK_BASE_URL",
        "https://api.deepseek.com",
    )

    if not api_key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY is not configured. Please check your .env file."
        )

    return OpenAI(
        api_key=api_key,
        base_url=base_url,
    )


def get_model_name() -> str:

    model = os.getenv("DEEPSEEK_MODEL")

    if not model:
        raise RuntimeError("DEEPSEEK_MODEL is not configured.")

    return model
