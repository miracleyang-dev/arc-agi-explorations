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


# --- extension pack (v2, 7/11 PM): directional recolor, object ops -----------

def _map_color(a: int, b: int) -> Callable[[Grid], Grid]:
    """Directional recolor: every a becomes b. Non-a cells unchanged.
    Distinct from _swap_colors, which is symmetric."""
    def f(g: Grid) -> Grid:
        return tuple(tuple(b if v == a else v for v in row) for row in g)
    return f


def _keep_only_color(c: int) -> Callable[[Grid], Grid]:
    """Everything not equal to c becomes 0 (background)."""
    def f(g: Grid) -> Grid:
        return tuple(tuple(v if v == c else 0 for v in row) for row in g)
    return f


def _gravity(direction: str) -> Callable[[Grid], Grid]:
    """Pull all non-zero cells to the given edge, keeping relative order.
    Zeros collapse to the opposite side."""
    def f(g: Grid) -> Grid:
        if not g:
            return g
        h, w = len(g), len(g[0])
        if direction in ("up", "down"):
            new_cols: list[list[int]] = []
            for c in range(w):
                col = [g[r][c] for r in range(h)]
                nz = [v for v in col if v != 0]
                pad = [0] * (h - len(nz))
                new_cols.append(pad + nz if direction == "down" else nz + pad)
            return tuple(tuple(new_cols[c][r] for c in range(w)) for r in range(h))
        # left / right
        out = []
        for row in g:
            nz = [v for v in row if v != 0]
            pad = [0] * (w - len(nz))
            out.append(tuple(pad + nz if direction == "right" else nz + pad))
        return tuple(out)
    return f


def _crop_bbox_nonzero(g: Grid) -> Grid:
    """Crop to the bounding box of non-zero cells. All-zero grid returned as-is."""
    if not g:
        return g
    h, w = len(g), len(g[0])
    rmin, rmax, cmin, cmax = h, -1, w, -1
    for r in range(h):
        for c in range(w):
            if g[r][c] != 0:
                if r < rmin:
                    rmin = r
                if r > rmax:
                    rmax = r
                if c < cmin:
                    cmin = c
                if c > cmax:
                    cmax = c
    if rmax < 0:  # all zeros
        return g
    return tuple(tuple(g[r][cmin:cmax + 1]) for r in range(rmin, rmax + 1))


def _anti_transpose(g: Grid) -> Grid:
    """Flip along the anti-diagonal: element (r,c) -> position (w-1-c, h-1-r).
    Combined with the other 6 sym ops, gives the full dihedral group D4 at depth 1."""
    if not g:
        return g
    h, w = len(g), len(g[0])
    return tuple(
        tuple(g[h - 1 - c][w - 1 - r] for r in range(h))
        for c in range(w)
    )


def _scale(k: int) -> Callable[[Grid], Grid]:
    """Each cell becomes a k*k block (output is h*k by w*k)."""
    def f(g: Grid) -> Grid:
        out = []
        for row in g:
            expanded = tuple(v for v in row for _ in range(k))
            for _ in range(k):
                out.append(expanded)
        return tuple(out)
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
        # Full dihedral D4 symmetry group (7 non-identity ops).
        ("rot90", _rot90),
        ("rot180", _rot180),
        ("rot270", _rot270),
        ("flip_h", _flip_h),
        ("flip_v", _flip_v),
        ("transpose", _transpose),
        ("anti_transpose", _anti_transpose),
        # Reshape.
        ("tile_2x2", _tile_2x2),
        ("crop_tl_half", _crop_top_left_half),
        ("crop_bbox_nz", _crop_bbox_nonzero),
        ("scale_2", _scale(2)),
        ("scale_3", _scale(3)),
        # Gravity family.
        ("gravity_up", _gravity("up")),
        ("gravity_down", _gravity("down")),
        ("gravity_left", _gravity("left")),
        ("gravity_right", _gravity("right")),
    ]
    # Symmetric color swap (a,b unordered): 45 primitives.
    for a in range(10):
        for b in range(a + 1, 10):
            prims.append((f"swap_{a}_{b}", _swap_colors(a, b)))
    # Directional recolor a -> b (a != b): 90 primitives.
    # Complements swap_a_b when the true task recolors only one direction
    # (e.g. "turn all reds green" without touching greens).
    for a in range(10):
        for b in range(10):
            if a == b:
                continue
            prims.append((f"map_{a}_to_{b}", _map_color(a, b)))
    # Background fill: replace 0 with color c.
    for c in range(1, 10):
        prims.append((f"fill_bg_{c}", _fill_bg_with(c)))
    # Keep-only-one-color mask (object extraction).
    for c in range(1, 10):
        prims.append((f"keep_only_{c}", _keep_only_color(c)))
    return prims
