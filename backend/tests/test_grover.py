import numpy as np

from app.quantum.grover import WindowRunner
from app.quantum.propagation import candidates
from app.quantum.window import choose_window
from app.services.generator import generate_puzzle


def _runner(seed=1, budget=14):
    puzzle = generate_puzzle(30, seed=seed)["grid"]
    cells, n_data = choose_window(candidates(puzzle), budget)
    return WindowRunner(cells, n_data)


def test_amplification_beats_uniform_baseline():
    r = _runner()
    base_p, m = r.stats(np.full(r.N, 1 / r.N))
    assert m and 0 < m < r.N
    best = max(r.stats(r.probabilities_after(k))[0] for k in range(1, 8))
    assert best > base_p + 0.05


def test_run_finds_only_valid_states():
    r = _runner(seed=2)
    res = r.run(shots=64, rng=np.random.default_rng(0), max_attempts=10)
    assert res["found_states"]
    assert all(r.valid(s) for s in res["found_states"])
    assert res["total_iterations"] >= 1
    assert abs(sum(o["p"] for o in r.outcomes(r.probabilities_after(2), r.N)) - 1) < 1e-6
