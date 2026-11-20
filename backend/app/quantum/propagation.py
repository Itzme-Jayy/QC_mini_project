"""Classical constraint propagation (naked singles and hidden singles).

This shrinks every empty cell's candidate set before any qubits are spent. It only
applies Sudoku logic, so it never removes a candidate that belongs to a valid solution.
"""
from ..core.geometry import get_geometry


def candidates(grid):
    """cands[p] = sorted legal digits for an empty cell p given the filled peers; [] for filled cells."""
    num_cells = len(grid)
    geom = get_geometry(num_cells)
    size = geom.size
    out = []
    for p in range(num_cells):
        if grid[p]:
            out.append([])
        else:
            used = {grid[q] for q in geom.peers[p] if grid[q]}
            out.append([d for d in range(1, size + 1) if d not in used])
    return out


def propagate(grid, use_singles=True):
    """Return (grid, cands, ok, assigned_positions).

    ok is False when a contradiction is found (a cell or a unit digit with no place left).
    """
    num_cells = len(grid)
    geom = get_geometry(num_cells)
    size = geom.size
    g = list(grid)
    assigned = []
    while True:
        cands = candidates(g)
        if any(g[p] == 0 and not cands[p] for p in range(num_cells)):
            return g, cands, False, assigned
        if not use_singles:
            break
        changed = False
        for p in range(num_cells):  # naked singles
            if g[p] == 0 and len(cands[p]) == 1:
                g[p] = cands[p][0]
                assigned.append(p)
                changed = True
                break
        if changed:
            continue
        for unit in geom.units:  # hidden singles
            present = {g[p] for p in unit if g[p]}
            for d in range(1, size + 1):
                if d in present:
                    continue
                places = [p for p in unit if g[p] == 0 and d in cands[p]]
                if not places:
                    return g, cands, False, assigned
                if len(places) == 1:
                    g[places[0]] = d
                    assigned.append(places[0])
                    changed = True
                    break
            if changed:
                break
        if not changed:
            break
    clash = any(g[p] and any(g[q] == g[p] for q in geom.peers[p]) for p in range(num_cells))
    return g, candidates(g), not clash, assigned
