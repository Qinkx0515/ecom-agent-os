from contextlib import contextmanager
from pathlib import Path

from langgraph.checkpoint.sqlite import (
    SqliteSaver,
)

DEFAULT_CHECKPOINT_PATH = Path("data/checkpoints/commerce.sqlite3")


@contextmanager
def create_sqlite_checkpointer(
    path: Path = DEFAULT_CHECKPOINT_PATH,
):

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with SqliteSaver.from_conn_string(str(path)) as checkpointer:
        yield checkpointer
