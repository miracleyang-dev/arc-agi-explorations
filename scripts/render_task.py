"""
Render an ARC task as a single PNG: all train pairs + all test pairs (input only,
or input+output if solved). Output saved to notes/img/<task_id>.png.

Usage (from repo root):
    python scripts/render_task.py 007bbfb7
    python scripts/render_task.py 007bbfb7 --dataset arc-agi-2
    python scripts/render_task.py --all              # render every task in data/arc-agi-1/training
    python scripts/render_task.py --ids 007bbfb7 00d62c1b 05f2a901

Assumes repo layout:
    data/arc-agi-1/training/<task_id>.json
    data/arc-agi-1/evaluation/<task_id>.json
    data/arc-agi-2/training/<task_id>.json
    data/arc-agi-2/evaluation/<task_id>.json
"""

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap, BoundaryNorm

# Official ARC palette (index 0..9).
ARC_COLORS = [
    "#000000",  # 0 black
    "#0074D9",  # 1 blue
    "#FF4136",  # 2 red
    "#2ECC40",  # 3 green
    "#FFDC00",  # 4 yellow
    "#AAAAAA",  # 5 grey
    "#F012BE",  # 6 magenta
    "#FF851B",  # 7 orange
    "#7FDBFF",  # 8 sky
    "#870C25",  # 9 maroon
]
CMAP = ListedColormap(ARC_COLORS)
NORM = BoundaryNorm(boundaries=list(range(11)), ncolors=10)


def _find_task(task_id: str, dataset: str) -> Path:
    """Search training then evaluation split for the given task_id."""
    root = Path("data") / dataset
    for split in ("training", "evaluation"):
        p = root / split / f"{task_id}.json"
        if p.exists():
            return p
    raise FileNotFoundError(
        f"Task {task_id} not found under {root}/{{training,evaluation}}. "
        f"Check the ID or --dataset flag."
    )


def _draw_grid(ax, grid, title: str):
    """Render one grid on the given axis with cell borders and title."""
    arr = np.array(grid, dtype=int)
    ax.imshow(arr, cmap=CMAP, norm=NORM, interpolation="nearest")
    ax.set_xticks(np.arange(-0.5, arr.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, arr.shape[0], 1), minor=True)
    ax.grid(which="minor", color="#333333", linewidth=0.5)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, fontsize=9)


def render_task(task_id: str, dataset: str, out_dir: Path) -> Path:
    task_path = _find_task(task_id, dataset)
    with open(task_path, "r", encoding="utf-8") as f:
        task = json.load(f)

    train_pairs = task["train"]
    test_pairs = task["test"]
    n_train = len(train_pairs)
    n_test = len(test_pairs)
    n_cols = n_train + n_test

    fig, axes = plt.subplots(
        2, n_cols,
        figsize=(2.2 * n_cols, 4.6),
        squeeze=False,
    )

    for i, pair in enumerate(train_pairs):
        _draw_grid(axes[0, i], pair["input"], f"train {i} · input")
        _draw_grid(axes[1, i], pair["output"], f"train {i} · output")

    for j, pair in enumerate(test_pairs):
        col = n_train + j
        _draw_grid(axes[0, col], pair["input"], f"test {j} · input")
        if "output" in pair and pair["output"] is not None:
            _draw_grid(axes[1, col], pair["output"], f"test {j} · output")
        else:
            axes[1, col].axis("off")
            axes[1, col].text(0.5, 0.5, "?", ha="center", va="center",
                              fontsize=32, color="#888888",
                              transform=axes[1, col].transAxes)
            axes[1, col].set_title(f"test {j} · output", fontsize=9)

    fig.suptitle(f"{task_id}  ({dataset} / {task_path.parent.name})", fontsize=11)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{task_id}.png"
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task_id", nargs="?", help="Single task id (8 hex chars)")
    ap.add_argument("--ids", nargs="+", help="Multiple task ids")
    ap.add_argument("--all", action="store_true",
                    help="Render every task in the training split of --dataset")
    ap.add_argument("--dataset", default="arc-agi-1",
                    choices=["arc-agi-1", "arc-agi-2"])
    ap.add_argument("--out", default="notes/img", help="Output directory")
    args = ap.parse_args()

    out_dir = Path(args.out)

    if args.all:
        ids = sorted(p.stem for p in
                     (Path("data") / args.dataset / "training").glob("*.json"))
    elif args.ids:
        ids = args.ids
    elif args.task_id:
        ids = [args.task_id]
    else:
        ap.error("Provide task_id, --ids, or --all")

    ok, fail = 0, []
    for tid in ids:
        try:
            path = render_task(tid, args.dataset, out_dir)
            print(f"[OK]  {tid} -> {path}")
            ok += 1
        except FileNotFoundError as e:
            print(f"[MISS] {e}", file=sys.stderr)
            fail.append(tid)
    print(f"\nRendered {ok}/{len(ids)}. Missing: {fail if fail else 'none'}")


if __name__ == "__main__":
    main()
