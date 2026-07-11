"""
Minimal DSL for the MVP solver.

Design intent (7/11):
  - Start with ~15 primitives covering the most common ARC-1 abstractions:
    identity, geometric (rotate/flip/transpose), color remap, cropping,
    tiling, single-color fill.
  - Every primitive is a pure function Grid -> Grid, deterministic, cheap.
  - No parameters left to search over inside a primitive: all parameters
    are either fixed (e.g. rot90) or enumerated at the search-tree level
    (e.g. one primitive per possible color swap pair).
  - Composition depth is capped at 2 in the baseline runner — icecuber's
    2020 result showed depth-2 covers a big chunk of "easy" tasks.

This file intentionally does NOT try to be Hodel-complete. Hodel's DSL
(~800 primitives) is planned as a submodule after Direction A is fixed.
"""

from __future__ import annotations

from typing import Callable

from .loader import Grid

# A primitive = (name, function). Function takes a Grid, returns a Grid.
Primitive = tuple[str, Callable[[Grid], Grid]]


# --- geometric ---------------------------------------------------------------

def _identity(g: Grid) -> Grid:
    return g


def _rot90(g: Grid) -> Grid:
    # Rotate 90 degrees clockwise.
    h = len(g)
    if h == 0:
        return g
    w = len(g[0])
    return tuple(tuple(g[h - 1 - r][c] for r in range(h)) for c in range(w))


def _rot180(g: Grid) -> Grid:
    return tuple(tuple(reversed(row)) for row in reversed(g))


def _rot270(g: Grid) -> Grid:
    return _rot90(_rot180(g))


def _flip_h(g: Grid) -> Grid:
    return tuple(tuple(reversed(row)) for row in g)


def _flip_v(g: Grid) -> Grid:
    return tuple(reversed(g))


def _transpose(g: Grid) -> Grid:
    if not g:
        return g
    return tuple(tuple(g[r][c] for r in range(len(g))) for c in range(len(g[0])))


# --- color -------------------------------------------------------------------

def _swap_colors(a: int, b: int) -> Callable[[Grid], Grid]:
    def f(g: Grid) -> Grid:
        return tuple(
            tuple(b if v == a else (a if v == b else v) for v in row)
            for row in g
        )
    return f


# --- tiling / cropping -------------------------------------------------------

def _tile_2x2(g: Grid) -> Grid:
    """Duplicate the grid to form a 2x2 mosaic."""
    top = tuple(row + row for row in g)
    return top + top


def _crop_top_left_half(g: Grid) -> Grid:
    """Return the top-left quadrant (integer half). Undefined for size<2."""
    h, w = len(g), (len(g[0]) if g else 0)
    if h < 2 or w < 2:
        return g
    return tuple(row[: w // 2] for row in g[: h // 2])


# --- fill --------------------------------------------------------------------

def _fill_bg_with(color: int) -> Callable[[Grid], Grid]:
    """Replace every 0 (background) with `color`."""
    def f(g: Grid) -> Grid:
        return tuple(tuple(color if v == 0 else v for v in row) for row in g)
    return f


# --- registry ----------------------------------------------------------------

def build_primitives() -> list[Primitive]:
    """
    Instantiate every concrete primitive.

    Color-parameterized primitives are unrolled: for `swap_colors(a,b)` we
    emit one primitive per (a<b) pair in 0..9 (45 primitives), so the
    downstream search doesn't need to know about parameters.
    """
    prims: list[Primitive] = [
        ("identity", _identity),
        ("rot90", _rot90),
        ("rot180", _rot180),
        ("rot270", _rot270),
        ("flip_h", _flip_h),
        ("flip_v", _flip_v),
        ("transpose", _transpose),
        ("tile_2x2", _tile_2x2),
        ("crop_tl_half", _crop_top_left_half),
    ]
    for a in range(10):
        for b in range(a + 1, 10):
            prims.append((f"swap_{a}_{b}", _swap_colors(a, b)))
    for c in range(1, 10):
        prims.append((f"fill_bg_{c}", _fill_bg_with(c)))
    return prims
