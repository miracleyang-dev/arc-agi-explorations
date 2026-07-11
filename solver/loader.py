"""
Task loader.

An ARC task JSON has schema:
    {
      "train": [{"input": Grid, "output": Grid}, ...],  # >=1 pair
      "test":  [{"input": Grid, "output": Grid?}, ...]  # >=1 pair; output may
                                                       #  be absent on hidden set
    }
where Grid = List[List[int]], values in 0..9.

We keep grids as tuple-of-tuple internally: hashable, immutable, cheap to copy.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

Grid = tuple[tuple[int, ...], ...]


def _to_grid(rows: list[list[int]]) -> Grid:
    return tuple(tuple(int(v) for v in r) for r in rows)


@dataclass(frozen=True)
class Pair:
    input: Grid
    output: Grid | None  # None only for hidden test inputs


@dataclass(frozen=True)
class Task:
    task_id: str
    train: tuple[Pair, ...]
    test: tuple[Pair, ...]

    @property
    def n_train(self) -> int:
        return len(self.train)

    @property
    def n_test(self) -> int:
        return len(self.test)


def load_task(path: Path) -> Task:
    """Load one <task_id>.json file into a Task."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    train = tuple(
        Pair(_to_grid(p["input"]), _to_grid(p["output"]))
        for p in data["train"]
    )
    test = tuple(
        Pair(
            _to_grid(p["input"]),
            _to_grid(p["output"]) if p.get("output") is not None else None,
        )
        for p in data["test"]
    )
    return Task(task_id=path.stem, train=train, test=test)


def iter_split(data_root: Path, dataset: str, split: str):
    """Yield (task_id, Task) for every JSON in data/<dataset>/<split>/."""
    split_dir = data_root / dataset / split
    if not split_dir.exists():
        raise FileNotFoundError(
            f"{split_dir} not found. Run `python scripts/fetch_data.py` first."
        )
    for path in sorted(split_dir.glob("*.json")):
        yield path.stem, load_task(path)
