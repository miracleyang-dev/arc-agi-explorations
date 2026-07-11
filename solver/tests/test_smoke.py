"""
Smoke tests: no external data required.

We construct synthetic ARC-shaped tasks whose ground truth is known
(e.g. "output = rot90(input)"), then assert the brute-force searcher
finds a program that matches.

Run:
    pytest solver/tests
or:
    python -m solver.tests.test_smoke   # standalone, no pytest needed
"""

from __future__ import annotations

from solver.dsl import build_primitives, _rot90, _flip_h, _swap_colors
from solver.loader import Pair, Task
from solver.search import search_task


def _mk_task(task_id: str, transform, inputs):
    """Build a Task where every train output = transform(input)."""
    train = tuple(Pair(inp, transform(inp)) for inp in inputs[:-1])
    test = (Pair(inputs[-1], transform(inputs[-1])),)
    return Task(task_id=task_id, train=train, test=test)


def _g(*rows):
    return tuple(tuple(r) for r in rows)


def test_identity_depth1():
    prims = build_primitives()
    task = _mk_task("t_id", lambda g: g,
                    [_g([1, 0], [0, 1]), _g([2, 2], [3, 3]), _g([1, 2, 3])])
    res = search_task(task, prims, max_depth=1, time_budget_sec=2.0)
    assert res.solved, "identity task should be solved at depth 1"
    assert res.depth == 1


def test_rot90_depth1():
    prims = build_primitives()
    task = _mk_task("t_rot", _rot90,
                    [_g([1, 2], [3, 4]), _g([0, 1, 0], [1, 0, 1])])
    res = search_task(task, prims, max_depth=1, time_budget_sec=2.0)
    assert res.solved
    assert res.program == ["rot90"]


def test_swap_colors_depth1():
    prims = build_primitives()
    swap = _swap_colors(1, 2)
    # Deliberately asymmetric grids so no geometric primitive can accidentally
    # produce the same output — forces the searcher onto swap_1_2.
    task = _mk_task("t_swap", swap,
                    [_g([1, 1, 1], [1, 2, 1]), _g([2, 1, 2], [1, 1, 1])])
    res = search_task(task, prims, max_depth=1, time_budget_sec=2.0)
    assert res.solved
    assert res.program == ["swap_1_2"], f"got {res.program}"


def test_composed_depth2():
    """flip_h then rot90 — must be found at depth 2, not depth 1."""
    prims = build_primitives()
    task = _mk_task("t_comp", lambda g: _rot90(_flip_h(g)),
                    [_g([1, 2, 3], [4, 5, 6]), _g([0, 1], [1, 0])])
    # depth 1 alone should fail.
    res1 = search_task(task, prims, max_depth=1, time_budget_sec=2.0)
    assert not res1.solved
    # depth 2 succeeds.
    res2 = search_task(task, prims, max_depth=2, time_budget_sec=10.0)
    assert res2.solved
    assert res2.depth == 2
    # Note: several depth-2 programs can produce the same output as
    # flip_h then rot90 (e.g. rot270 then flip_v). We only require *a*
    # valid depth-2 program is found, not the specific one we authored.
    assert res2.program is not None and len(res2.program) == 2


def test_unsolvable_bail_within_budget():
    """A task with no depth<=2 solution must return solved=False, not hang."""
    prims = build_primitives()
    # Impossible: output is input with a single arbitrary cell mutated —
    # no primitive in our DSL can do surgical single-cell edits.
    # We need >=2 train pairs so a single lucky swap_a_b can't be confused
    # for the true transform. Both train inputs already contain 9, so no
    # swap involving 9 can "just add a 9 at (0,0)" without side-effects on
    # the other 9-cells. No DSL primitive at depth<=2 does surgical
    # single-cell mutations.
    task = _mk_task(
        "t_impossible",
        lambda g: tuple(tuple(9 if (r, c) == (0, 0) else v
                              for c, v in enumerate(row))
                        for r, row in enumerate(g)),
        [
            _g([1, 2, 9], [3, 4, 9], [9, 9, 5]),
            _g([2, 9, 1], [9, 3, 4], [7, 9, 6]),
            _g([0, 0], [0, 0]),
        ],
    )
    res = search_task(task, prims, max_depth=2, time_budget_sec=5.0)
    assert not res.solved
    assert res.elapsed_sec < 6.0  # budget-respecting


if __name__ == "__main__":
    # Standalone entry: no pytest required.
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  PASS  {name}")
    print("\nAll smoke tests passed.")
