from langfuse import get_client
from dotenv import load_dotenv
load_dotenv()


def get_langfuse_client():

    return get_client()


def check_langfuse_connection() -> bool:

    client = get_langfuse_client()

    return client.auth_check()


def flush_langfuse():

    client = get_langfuse_client()

    client.flush()


if __name__ == "__main__":

    success = (
        check_langfuse_connection()
    )

    print(
        f"Langfuse connected: "
        f"{success}"
    )