from app.classical.backtracking import count_solutions, solve
from app.services.generator import generate_puzzle
from app.services.validator import find_conflicts, is_complete_valid, preserves_givens


def test_solves_generated_puzzles_of_each_difficulty():
    for clues, seed in [(40, 1), (32, 2), (26, 3)]:
        p = generate_puzzle(clues, seed=seed)["grid"]
        r = solve(p)
        assert r["solutions"] and is_complete_valid(r["solutions"][0])
        assert preserves_givens(p, r["solutions"][0])
        assert r["nodes"] >= 1


def test_generated_puzzles_are_unique():
    assert count_solutions(generate_puzzle(30, seed=4)["grid"], limit=2) == 1


def test_detects_unsolvable_puzzle_without_direct_conflict():
    g = [0] * 81
    for c in range(1, 9):
        g[c] = c        # row 0 holds 1..8, so cell 0 needs 9 ...
    g[27] = 9           # ... but column 0 already has a 9
    assert find_conflicts(g) == []
    assert count_solutions(g, limit=1) == 0


def test_generator_differs_per_seed():
    assert generate_puzzle(35, seed=1)["grid"] != generate_puzzle(35, seed=2)["grid"]
