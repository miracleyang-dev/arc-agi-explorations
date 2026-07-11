# arc-agi-explorations

Reading notes, task analyses, and experiments on the **ARC-AGI** benchmark
(Chollet, 2019 — *On the Measure of Intelligence*).

This repository is a personal research notebook I keep during my summer
research internship at HKUST (Jul – Aug 2026). The goal is to build a
principled understanding of the ARC-AGI benchmark, its core priors, and
the current landscape of approaches, before attempting any new method.

## Layout

```
notes/       Paper-reading notes and task-taxonomy write-ups
scripts/     Utilities: render_task.py, fetch_data.py, setup_venv.bat
solver/      MVP brute-force DSL solver + smoke tests
data/        Ignored — ARC tasks are downloaded locally, not committed
```

## Setup (Windows, CMD)

One-time install:

```cmd
scripts\setup_venv.bat
```

This creates `.venv\`, upgrades pip, and installs runtime + dev deps.

Every new terminal after that:

```cmd
.venv\Scripts\activate
```

Fetch ARC-AGI-1 and ARC-AGI-2 raw JSON (idempotent, safe to re-run):

```cmd
python scripts\fetch_data.py
```

Quick verify:

```cmd
python -m solver.tests.test_smoke
python -m solver.runner --split training --max-tasks 5
```

## Planned notes

- `notes/01_chollet_summary.md` — key claims of *On the Measure of Intelligence*
- `notes/02_task_taxonomy.md`   — hand-solved tasks grouped by required prior
- `notes/03_landscape.md`       — recent ARC papers, methods, and scoreboards

## References

- Chollet, F. (2019). *On the Measure of Intelligence*. arXiv:1911.01547
- ARC-AGI dataset: https://github.com/fchollet/ARC-AGI
- ARC Prize: https://arcprize.org

---

Maintained by [@miracleyang-dev](https://github.com/miracleyang-dev).
Work in progress; notes may be rewritten without notice.
