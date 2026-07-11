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


# --- extension pack (v3, 7/11 PM): structured ops --------------------------
# After v2 (170 prims) saturated near 5%, we add operations that go beyond
# element-wise recolor and pure geometry:
#   - object-level (connected components with 4-connectivity)
#   - symmetry completion (half-mirror and OR-overlay)
#   - self-stacking (double the grid along an axis)
#   - shape reduction (drop empty rows/cols, binarize)
#   - flood-fill of enclosed background regions
# These are the last DSL additions we plan to make; further gains require
# breaking the pure Grid->Grid contract (counting, pattern completion), so
# after v3 we freeze the DSL and pivot to learned operators.


def _to_list(g: Grid) -> list[list[int]]:
    return [list(row) for row in g]


def _to_grid(g: list[list[int]]) -> Grid:
    return tuple(tuple(row) for row in g)


def _find_components(g: Grid) -> list[list[tuple[int, int]]]:
    """4-connected components over non-zero cells. Two cells with the same
    color and adjacent (4-neighborhood) go in the same component. Cells with
    value 0 (background) are excluded."""
    h, w = len(g), len(g[0]) if g else 0
    seen = [[False] * w for _ in range(h)]
    comps: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if seen[r][c] or g[r][c] == 0:
                continue
            color = g[r][c]
            stack = [(r, c)]
            comp: list[tuple[int, int]] = []
            while stack:
                y, x = stack.pop()
                if y < 0 or y >= h or x < 0 or x >= w:
                    continue
                if seen[y][x] or g[y][x] != color:
                    continue
                seen[y][x] = True
                comp.append((y, x))
                stack.extend([(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)])
            comps.append(comp)
    return comps


def _keep_largest_object(g: Grid) -> Grid:
    """Zero out everything except the largest 4-connected non-zero component.
    Ties broken by first-seen (top-left)."""
    comps = _find_components(g)
    if not comps:
        return g
    largest = max(comps, key=len)
    keep = set(largest)
    h, w = len(g), len(g[0])
    out = [[0] * w for _ in range(h)]
    for (r, c) in keep:
        out[r][c] = g[r][c]
    return _to_grid(out)


def _outline_objects(g: Grid) -> Grid:
    """For each object, keep only cells with at least one 0 or out-of-grid
    4-neighbor; zero the interior."""
    h, w = len(g), len(g[0]) if g else 0
    out = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if g[r][c] == 0:
                continue
            on_edge = False
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if nr < 0 or nr >= h or nc < 0 or nc >= w or g[nr][nc] == 0:
                    on_edge = True
                    break
            if on_edge:
                out[r][c] = g[r][c]
    return _to_grid(out)


def _interior_of_objects(g: Grid) -> Grid:
    """Inverse of outline: keep only cells whose 4 neighbors are all non-zero."""
    h, w = len(g), len(g[0]) if g else 0
    out = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if g[r][c] == 0:
                continue
            interior = True
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if nr < 0 or nr >= h or nc < 0 or nc >= w or g[nr][nc] == 0:
                    interior = False
                    break
            if interior:
                out[r][c] = g[r][c]
    return _to_grid(out)


# --- symmetry completion (half-mirror) ---

def _sym_h_from_left(g: Grid) -> Grid:
    """Copy the left half onto the right half (mirror). For odd width, the
    center column is preserved from the input."""
    if not g:
        return g
    w = len(g[0])
    half = w // 2
    out = []
    for row in g:
        new = list(row)
        for c in range(half):
            new[w - 1 - c] = row[c]
        out.append(tuple(new))
    return tuple(out)


def _sym_h_from_right(g: Grid) -> Grid:
    if not g:
        return g
    w = len(g[0])
    half = w // 2
    out = []
    for row in g:
        new = list(row)
        for c in range(half):
            new[c] = row[w - 1 - c]
        out.append(tuple(new))
    return tuple(out)


def _sym_v_from_top(g: Grid) -> Grid:
    if not g:
        return g
    h = len(g)
    half = h // 2
    out = _to_list(g)
    for r in range(half):
        out[h - 1 - r] = list(g[r])
    return _to_grid(out)


def _sym_v_from_bottom(g: Grid) -> Grid:
    if not g:
        return g
    h = len(g)
    half = h // 2
    out = _to_list(g)
    for r in range(half):
        out[r] = list(g[h - 1 - r])
    return _to_grid(out)


# --- symmetry overlay (OR two views) ---

def _overlay_max(g1: Grid, g2: Grid) -> Grid:
    """Element-wise max. Assumes both grids have identical shape."""
    return tuple(
        tuple(max(g1[r][c], g2[r][c]) for c in range(len(g1[0])))
        for r in range(len(g1))
    )


def _overlay_flip_h_or(g: Grid) -> Grid:
    return _overlay_max(g, _flip_h(g))


def _overlay_flip_v_or(g: Grid) -> Grid:
    return _overlay_max(g, _flip_v(g))


def _overlay_rot180_or(g: Grid) -> Grid:
    return _overlay_max(g, _rot180(g))


def _overlay_transpose_or(g: Grid) -> Grid:
    """Only defined for square grids; return input unchanged otherwise."""
    if not g or len(g) != len(g[0]):
        return g
    return _overlay_max(g, _transpose(g))


# --- self stacking ---

def _hcat_self(g: Grid) -> Grid:
    return tuple(row + row for row in g)


def _hcat_flip_h(g: Grid) -> Grid:
    return tuple(row + tuple(reversed(row)) for row in g)


def _vcat_self(g: Grid) -> Grid:
    return g + g


def _vcat_flip_v(g: Grid) -> Grid:
    return g + tuple(reversed(g))


# --- shape reduction ---

def _remove_empty_rows(g: Grid) -> Grid:
    kept = tuple(row for row in g if any(v != 0 for v in row))
    return kept if kept else g


def _remove_empty_cols(g: Grid) -> Grid:
    if not g:
        return g
    w = len(g[0])
    keep_c = [c for c in range(w) if any(row[c] != 0 for row in g)]
    if not keep_c:
        return g
    return tuple(tuple(row[c] for c in keep_c) for row in g)


def _binarize_nz_to_1(g: Grid) -> Grid:
    return tuple(tuple(1 if v != 0 else 0 for v in row) for row in g)


# --- enclosed-region flood fill ---

def _fill_enclosed_zero_with(color: int) -> Callable[[Grid], Grid]:
    """
    Any 0-cell not reachable from the grid border via 4-connected 0-cells is
    considered enclosed by non-zero cells; recolor those to `color`.
    Cells reachable from the border stay 0.
    """
    def f(g: Grid) -> Grid:
        if not g:
            return g
        h, w = len(g), len(g[0])
        reachable = [[False] * w for _ in range(h)]
        stack: list[tuple[int, int]] = []
        for r in range(h):
            for c in (0, w - 1):
                if g[r][c] == 0:
                    stack.append((r, c))
        for c in range(w):
            for r in (0, h - 1):
                if g[r][c] == 0:
                    stack.append((r, c))
        while stack:
            y, x = stack.pop()
            if y < 0 or y >= h or x < 0 or x >= w:
                continue
            if reachable[y][x] or g[y][x] != 0:
                continue
            reachable[y][x] = True
            stack.extend([(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)])
        out = _to_list(g)
        for r in range(h):
            for c in range(w):
                if g[r][c] == 0 and not reachable[r][c]:
                    out[r][c] = color
        return _to_grid(out)
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
    # v3 additions: structured operations.
    prims.extend([
        ("keep_largest_obj", _keep_largest_object),
        ("outline_objects", _outline_objects),
        ("interior_of_objects", _interior_of_objects),
        ("sym_h_from_left", _sym_h_from_left),
        ("sym_h_from_right", _sym_h_from_right),
        ("sym_v_from_top", _sym_v_from_top),
        ("sym_v_from_bottom", _sym_v_from_bottom),
        ("overlay_flip_h_or", _overlay_flip_h_or),
        ("overlay_flip_v_or", _overlay_flip_v_or),
        ("overlay_rot180_or", _overlay_rot180_or),
        ("overlay_transpose_or", _overlay_transpose_or),
        ("hcat_self", _hcat_self),
        ("hcat_flip_h", _hcat_flip_h),
        ("vcat_self", _vcat_self),
        ("vcat_flip_v", _vcat_flip_v),
        ("remove_empty_rows", _remove_empty_rows),
        ("remove_empty_cols", _remove_empty_cols),
        ("binarize_nz_to_1", _binarize_nz_to_1),
    ])
    for c in range(1, 10):
        prims.append((f"fill_enclosed_{c}", _fill_enclosed_zero_with(c)))
    return prims
