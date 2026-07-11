"""
End-to-end runner: iterate a split, solve each task, dump results to JSON.

Usage:
    python -m solver.runner                                   # 5-task smoke
    python -m solver.runner --split training --max-tasks 50
    python -m solver.runner --split training                  # full 400
    python -m solver.runner --split evaluation --depth 2 --budget 5

Output goes to solver/results/<dataset>_<split>_<timestamp>.json with:
    {
      "config": {...},
      "summary": {"n_tasks": ..., "n_solved": ..., "solve_rate": ...},
      "per_task": [{task_id, solved, program, depth, elapsed_sec}, ...]
    }

Predictions are NOT included in the summary JSON to keep it small; if you
need them (e.g. for `pass@2` scoring later), run scoring in a separate pass
from the recorded program string.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path

from .dsl import build_primitives
from .loader import iter_split
from .search import search_task


def run(
    data_root: Path,
    dataset: str,
    split: str,
    max_tasks: int | None,
    max_depth: int,
    time_budget_sec: float,
    out_dir: Path,
) -> Path:
    primitives = build_primitives()
    print(f"[init] DSL size: {len(primitives)} primitives, "
          f"max_depth={max_depth}, budget={time_budget_sec}s/task")

    records = []
    n_solved = 0
    t_start = time.time()
    for i, (task_id, task) in enumerate(iter_split(data_root, dataset, split)):
        if max_tasks is not None and i >= max_tasks:
            break
        res = search_task(task, primitives,
                          max_depth=max_depth, time_budget_sec=time_budget_sec)
        rec = {
            "task_id": res.task_id,
            "solved": res.solved,
            "program": res.program,
            "depth": res.depth,
            "elapsed_sec": round(res.elapsed_sec, 3),
        }
        records.append(rec)
        if res.solved:
            n_solved += 1
        flag = "OK " if res.solved else "-- "
        print(f"[{flag}] {i:>3} {task_id}  "
              f"depth={res.depth} prog={res.program} "
              f"({res.elapsed_sec:.2f}s)")

    total_elapsed = time.time() - t_start
    n_tasks = len(records)
    solve_rate = n_solved / n_tasks if n_tasks else 0.0
    print(f"\n[summary] solved {n_solved}/{n_tasks} "
          f"= {solve_rate:.1%} in {total_elapsed:.1f}s")

    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"{dataset}_{split}_{stamp}.json"
    payload = {
        "config": {
            "dataset": dataset,
            "split": split,
            "max_tasks": max_tasks,
            "max_depth": max_depth,
            "time_budget_sec": time_budget_sec,
            "n_primitives": len(primitives),
        },
        "summary": {
            "n_tasks": n_tasks,
            "n_solved": n_solved,
            "solve_rate": solve_rate,
            "total_elapsed_sec": round(total_elapsed, 2),
        },
        "per_task": records,
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[out] wrote {out_path}")
    return out_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default="data")
    ap.add_argument("--dataset", default="arc-agi-1",
                    choices=["arc-agi-1", "arc-agi-2"])
    ap.add_argument("--split", default="training",
                    choices=["training", "evaluation"])
    ap.add_argument("--max-tasks", type=int, default=5,
                    help="Cap number of tasks (default 5 = smoke test). "
                         "Use -1 for full split.")
    ap.add_argument("--depth", type=int, default=2,
                    help="Max program composition depth (default 2).")
    ap.add_argument("--budget", type=float, default=5.0,
                    help="Per-task time budget in seconds (default 5.0).")
    ap.add_argument("--out-dir", default="solver/results")
    args = ap.parse_args()

    max_tasks = None if args.max_tasks == -1 else args.max_tasks
    run(
        data_root=Path(args.data_root),
        dataset=args.dataset,
        split=args.split,
        max_tasks=max_tasks,
        max_depth=args.depth,
        time_budget_sec=args.budget,
        out_dir=Path(args.out_dir),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
