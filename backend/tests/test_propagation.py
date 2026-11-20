from app.classical.backtracking import solve
from app.quantum.propagation import candidates, propagate
from app.services.generator import generate_puzzle


def test_propagation_never_removes_the_true_digit():
    for seed in (1, 2, 3):
        puzzle = generate_puzzle(26, seed=seed)["grid"]
        truth = solve(puzzle)["solutions"][0]       # test oracle only
        g, cands, ok, assigned = propagate(puzzle)
        assert ok
        for p in range(81):
            if puzzle[p] == 0:
                assert g[p] == truth[p] or truth[p] in cands[p]
        for p in assigned:
            assert g[p] == truth[p]


def test_candidates_exclude_peers():
    g = [0] * 81
    g[1] = 4
    g[9] = 7
    c = candidates(g)
    assert 4 not in c[0] and 7 not in c[0]


def test_contradiction_is_reported():
    g = [0] * 81
    for c in range(1, 9):
        g[c] = c
    g[27] = 9
    assert propagate(g)[2] is False
