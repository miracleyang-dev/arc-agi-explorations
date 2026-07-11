"""
Brute-force program search over the DSL, capped at composition depth `max_depth`.

Semantics:
  - A "program" is a list of primitive names, applied left-to-right:
      program = [p1, p2, p3]  =>  output = p3(p2(p1(input)))
  - We accept a program iff it produces the exact expected output for
    *every* training pair (strict verification).
  - depth=1: N primitives.
  - depth=2: N*N primitives.
  - depth=3: N*N*N primitives (~500k for N=63 — feasible but slow, so cap at 2 by default).

Anytime early-exit: we return the FIRST program that verifies. That's a
deliberate MVP choice — icecuber's post-hoc selection with multiple valid
programs is a Direction A refinement, not a day-1 concern.
"""

from __future__ import annotations

import itertools
import time
from dataclasses import dataclass

from .dsl import Primitive
from .loader import Grid, Task


@dataclass
class SolveResult:
    task_id: str
    solved: bool
    program: list[str] | None       # e.g. ["rot90", "swap_1_2"]
    predictions: list[Grid] | None  # one per test input; None if unsolved
    depth: int | None               # depth at which we found a solution
    elapsed_sec: float


def _apply_program(prims_by_name: dict, program: tuple[str, ...], g: Grid) -> Grid:
    for name in program:
        g = prims_by_name[name](g)
    return g


def _verifies_on_train(
    prims_by_name: dict, program: tuple[str, ...], task: Task
) -> bool:
    for pair in task.train:
        try:
            got = _apply_program(prims_by_name, program, pair.input)
        except Exception:  # noqa: BLE001 — a bad primitive shouldn't crash the run
            return False
        if got != pair.output:
            return False
    return True


def search_task(
    task: Task,
    primitives: list[Primitive],
    max_depth: int = 2,
    time_budget_sec: float = 5.0,
) -> SolveResult:
    """
    Enumerate programs of length 1..max_depth. Return the first one that
    reproduces all train outputs, then apply it to test inputs.

    time_budget_sec is a soft cap: we check it between candidate programs,
    so a runaway single-primitive call could still overshoot slightly.
    """
    t0 = time.time()
    prims_by_name = {name: fn for name, fn in primitives}
    names = [name for name, _ in primitives]

    for depth in range(1, max_depth + 1):
        for program in itertools.product(names, repeat=depth):
            if time.time() - t0 > time_budget_sec:
                return SolveResult(
                    task_id=task.task_id,
                    solved=False,
                    program=None,
                    predictions=None,
                    depth=None,
                    elapsed_sec=time.time() - t0,
                )
            if _verifies_on_train(prims_by_name, program, task):
                # Apply the winning program to all test inputs.
                try:
                    preds = [
                        _apply_program(prims_by_name, program, p.input)
                        for p in task.test
                    ]
                except Exception:  # noqa: BLE001
                    continue
                return SolveResult(
                    task_id=task.task_id,
                    solved=True,
                    program=list(program),
                    predictions=preds,
                    depth=depth,
                    elapsed_sec=time.time() - t0,
                )

    return SolveResult(
        task_id=task.task_id,
        solved=False,
        program=None,
        predictions=None,
        depth=None,
        elapsed_sec=time.time() - t0,
    )
