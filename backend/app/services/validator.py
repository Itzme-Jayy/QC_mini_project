"""Input parsing and Sudoku rule checking for 9x9 and 4x4 boards."""
from ..core.geometry import get_geometry


def parse_grid(data):
    """Accept a list of 81 or 16 ints, a 9x9 or 4x4 nested list, or an 81- or 16-char string.

    Returns a flat list of ints or raises ValueError.
    """
    if isinstance(data, str):
        s = data.strip().replace(".", "0")
        if len(s) not in (16, 81) or not s.isdigit():
            raise ValueError("Grid string must contain exactly 16 or 81 digits (0 or . for empty).")
        max_d = 4 if len(s) == 16 else 9
        out = [int(ch) for ch in s]
        for i, v in enumerate(out):
            if v > max_d:
                raise ValueError(f"Cell {i} must be an integer from 0 to {max_d}.")
        return out
    if isinstance(data, (list, tuple)):
        if (len(data) == 9 or len(data) == 4) and all(isinstance(r, (list, tuple)) for r in data):
            data = [v for r in data for v in r]
        if len(data) not in (16, 81):
            raise ValueError(f"Grid must have 16 or 81 cells, got {len(data)}.")
        max_d = 4 if len(data) == 16 else 9
        out = []
        for i, v in enumerate(data):
            if isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= max_d:
                raise ValueError(f"Cell {i} must be an integer from 0 to {max_d}.")
            out.append(v)
        return out
    raise ValueError("Grid must be a list of 16 or 81 integers or a string of 16 or 81 digits.")


def find_conflicts(grid):
    """Return sorted list of cell positions that clash with a peer holding the same digit."""
    geom = get_geometry(len(grid))
    bad = set()
    for p, v in enumerate(grid):
        if v and any(grid[q] == v for q in geom.peers[p]):
            bad.add(p)
    return sorted(bad)


def is_complete_valid(grid):
    """True if the grid is full and every row, column and box holds digits once."""
    num_cells = len(grid)
    if num_cells not in (16, 81):
        return False
    geom = get_geometry(num_cells)
    size = geom.size
    expected = list(range(1, size + 1))
    if any(v not in expected for v in grid):
        return False
    return all(sorted(grid[p] for p in unit) == expected for unit in geom.units)


def preserves_givens(puzzle, solution):
    return all(g == 0 or g == s for g, s in zip(puzzle, solution))


def grid_to_str(grid):
    return "".join(str(v) for v in grid)
