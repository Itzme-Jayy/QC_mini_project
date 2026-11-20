"""Runtime puzzle generator: random full grid by randomized backtracking, then cell removal
while the puzzle keeps exactly one solution. Nothing is stored or looked up."""
import random

from ..classical.backtracking import count_solutions, solve


def difficulty_for(clues, size=9):
    if size == 4:
        return "easy" if clues >= 8 else "medium" if clues >= 6 else "hard"
    return "easy" if clues >= 36 else "medium" if clues >= 30 else "hard"


def generate_full_grid(rng, size=9):
    num_cells = size * size
    return solve([0] * num_cells, limit=1, rng=rng)["solutions"][0]


def generate_puzzle(clues=None, seed=None, size=9):
    if size == 4:
        target_clues = 6 if clues is None else max(4, min(14, int(clues)))
        num_cells = 16
    else:
        size = 9
        target_clues = 32 if clues is None else max(22, min(80, int(clues)))
        num_cells = 81

    rng = random.Random(seed)
    grid = generate_full_grid(rng, size=size)
    order = list(range(num_cells))
    rng.shuffle(order)
    remaining = num_cells
    for p in order:
        if remaining <= target_clues:
            break
        keep = grid[p]
        grid[p] = 0
        if count_solutions(grid, limit=2) != 1:
            grid[p] = keep
        else:
            remaining -= 1
    return {"grid": grid, "clues": remaining, "difficulty": difficulty_for(remaining, size=size), "size": size}
