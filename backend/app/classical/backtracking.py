"""Classical backtracking solver with the MRV (minimum remaining values) heuristic.

Used for the comparison feature, puzzle generation and a solvability pre-check.
It never feeds answers into the quantum solver.
"""
import time

from ..core.geometry import get_geometry


def solve(grid, *, limit=1, rng=None):
    """Search for up to `limit` solutions.

    rng: optional random.Random; shuffles digit order (used by the generator).
    Returns dict(solutions, nodes, backtracks, time_ms). `nodes` counts placements tried.
    """
    start = time.perf_counter()
    num_cells = len(grid)
    geom = get_geometry(num_cells)
    size = geom.size
    all_mask = (1 << (size + 1)) - 2

    def _bits(mask):
        return [d for d in range(1, size + 1) if (mask >> d) & 1]

    g = list(grid)
    stats = {"nodes": 0, "backtracks": 0}
    solutions = []

    def cands(p):
        used = 0
        for q in geom.peers[p]:
            if g[q]:
                used |= 1 << g[q]
        return all_mask & ~used

    def search():
        best, best_mask, best_n = None, 0, size + 1
        for p in range(num_cells):
            if g[p] == 0:
                m = cands(p)
                n = bin(m).count("1")
                if n < best_n:
                    best, best_mask, best_n = p, m, n
                    if n <= 1:
                        break
        if best is None:
            solutions.append(list(g))
            return len(solutions) >= limit
        digits = _bits(best_mask)
        if rng is not None:
            rng.shuffle(digits)
        for d in digits:
            g[best] = d
            stats["nodes"] += 1
            if search():
                g[best] = 0
                return True
            g[best] = 0
            stats["backtracks"] += 1
        return False

    search()
    return {
        "solutions": solutions, "nodes": stats["nodes"], "backtracks": stats["backtracks"],
        "time_ms": (time.perf_counter() - start) * 1000,
    }


def count_solutions(grid, limit=2):
    return len(solve(grid, limit=limit)["solutions"])
