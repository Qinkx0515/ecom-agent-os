import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar(
    "T",
    bound=BaseModel,
)


def load_jsonl(
    path: Path,
    model_class: type[T],
) -> list[T]:

    cases: list[T] = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line_number, line in enumerate(
            file,
            start=1,
        ):
            line = line.strip()

            if not line:
                continue

            try:
                data = json.loads(line)

                cases.append(model_class.model_validate(data))

            except Exception as exc:
                raise RuntimeError(
                    f"Invalid eval case at {path}:{line_number}: {exc}"
                ) from exc

    return cases
