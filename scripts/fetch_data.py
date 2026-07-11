"""
Fetch ARC-AGI-1 and ARC-AGI-2 raw task JSONs from the official GitHub repos
into the local `data/` tree.

Target layout (matches scripts/render_task.py and solver/):
    data/arc-agi-1/training/<task_id>.json
    data/arc-agi-1/evaluation/<task_id>.json
    data/arc-agi-2/training/<task_id>.json
    data/arc-agi-2/evaluation/<task_id>.json

Idempotent: if a target file already exists (and --force is not passed),
we skip it and do NOT re-download. Never overwrites without --force.

Usage (from repo root):
    python scripts/fetch_data.py               # both datasets
    python scripts/fetch_data.py --v1          # ARC-AGI-1 only
    python scripts/fetch_data.py --v2          # ARC-AGI-2 only
    python scripts/fetch_data.py --force       # re-download even if present

Sources:
    ARC-AGI-1: github.com/fchollet/ARC-AGI       (data/{training,evaluation})
    ARC-AGI-2: github.com/arcprize/ARC-AGI-2     (data/{training,evaluation})

Both repos expose raw JSONs via GitHub's REST contents API, no auth required
for public repos (60 req/hour anon; we cap at 2 datasets * 2 splits = 4 API
calls to list, then N file downloads via raw.githubusercontent.com which is
not rate-limited).
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Repo config: (dataset_local_name, gh_owner, gh_repo, gh_branch)
DATASETS = {
    "arc-agi-1": ("fchollet", "ARC-AGI", "master"),
    "arc-agi-2": ("arcprize", "ARC-AGI-2", "main"),
}
SPLITS = ("training", "evaluation")

# Concurrency: raw.githubusercontent is fine with modest parallelism.
MAX_WORKERS = 16
TIMEOUT_SEC = 30


def _list_split(owner: str, repo: str, branch: str, split: str) -> list[str]:
    """Return list of task filenames (e.g. '007bbfb7.json') for a split."""
    api = (
        f"https://api.github.com/repos/{owner}/{repo}/contents/"
        f"data/{split}?ref={branch}"
    )
    req = urllib.request.Request(api, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
        entries = json.loads(resp.read().decode("utf-8"))
    return [e["name"] for e in entries if e["name"].endswith(".json")]


def _raw_url(owner: str, repo: str, branch: str, split: str, fname: str) -> str:
    return (
        f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/"
        f"data/{split}/{fname}"
    )


def _download(url: str, dest: Path) -> tuple[Path, bool, str | None]:
    """Download url -> dest. Returns (dest, ok, error_msg_or_None)."""
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SEC) as resp:
            data = resp.read()
        # Validate JSON before writing to disk.
        json.loads(data.decode("utf-8"))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return dest, True, None
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as e:
        return dest, False, str(e)


def fetch_split(
    dataset: str,
    owner: str,
    repo: str,
    branch: str,
    split: str,
    data_root: Path,
    force: bool,
) -> tuple[int, int, int]:
    """
    Fetch one (dataset, split) pair.

    Returns (n_total, n_downloaded, n_skipped_existing).
    """
    dest_dir = data_root / dataset / split
    print(f"[list] {dataset}/{split} -> github.com/{owner}/{repo}@{branch}")
    try:
        fnames = _list_split(owner, repo, branch, split)
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        print(f"[ERR ] failed to list {dataset}/{split}: {e}", file=sys.stderr)
        return 0, 0, 0

    to_fetch: list[tuple[str, Path]] = []
    skipped = 0
    for fname in fnames:
        dest = dest_dir / fname
        if dest.exists() and not force:
            skipped += 1
            continue
        to_fetch.append((_raw_url(owner, repo, branch, split, fname), dest))

    print(f"[plan] {dataset}/{split}: {len(fnames)} total, "
          f"{skipped} already present, {len(to_fetch)} to download")

    if not to_fetch:
        return len(fnames), 0, skipped

    ok = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futs = [pool.submit(_download, url, dest) for url, dest in to_fetch]
        for i, fut in enumerate(as_completed(futs), 1):
            dest, success, err = fut.result()
            if success:
                ok += 1
            else:
                print(f"[FAIL] {dest.name}: {err}", file=sys.stderr)
            if i % 50 == 0 or i == len(futs):
                print(f"       downloaded {i}/{len(futs)}")

    print(f"[done] {dataset}/{split}: +{ok} new, {skipped} kept")
    return len(fnames), ok, skipped


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v1", action="store_true", help="Fetch ARC-AGI-1 only")
    ap.add_argument("--v2", action="store_true", help="Fetch ARC-AGI-2 only")
    ap.add_argument("--force", action="store_true",
                    help="Re-download even if target file exists")
    ap.add_argument("--data-root", default="data",
                    help="Root directory to write into (default: ./data)")
    args = ap.parse_args()

    # Default = both datasets. Explicit --v1/--v2 narrows it.
    if not args.v1 and not args.v2:
        selected = list(DATASETS.keys())
    else:
        selected = []
        if args.v1:
            selected.append("arc-agi-1")
        if args.v2:
            selected.append("arc-agi-2")

    data_root = Path(args.data_root)
    grand_total = grand_new = grand_kept = 0
    for dataset in selected:
        owner, repo, branch = DATASETS[dataset]
        for split in SPLITS:
            n, new, kept = fetch_split(
                dataset, owner, repo, branch, split, data_root, args.force
            )
            grand_total += n
            grand_new += new
            grand_kept += kept

    print(
        f"\nSummary: {grand_total} tasks across "
        f"{len(selected)} datasets × {len(SPLITS)} splits "
        f"({grand_new} newly downloaded, {grand_kept} already present)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
