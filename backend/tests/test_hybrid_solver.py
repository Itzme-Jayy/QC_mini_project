from app.quantum import hybrid_solver
from app.services.generator import generate_puzzle
from app.services.validator import is_complete_valid, preserves_givens


def _check(puzzle, res):
    assert res["status"] == "solved"
    assert is_complete_valid(res["solution"])          # rules only, no stored answers
    assert preserves_givens(puzzle, res["solution"])


def test_solves_hard_puzzle_with_propagation():
    p = generate_puzzle(24, seed=5)["grid"]
    res = hybrid_solver.solve(p, qubit_budget=16, seed=1)
    _check(p, res)
    assert res["metrics"]["max_qubits"] <= 16


def test_quantum_windows_do_real_work_without_singles():
    p = generate_puzzle(42, seed=2)["grid"]
    res = hybrid_solver.solve(p, qubit_budget=12, use_singles=False, seed=1)
    _check(p, res)
    assert res["metrics"]["windows"] > 0 and res["metrics"]["grover_runs"] > 0
    assert res["metrics"]["iterations"] > 0
    kinds = {s["type"] for s in res["trace"]}
    assert {"window", "oracle", "diffusion", "measurement", "verification", "commit"} <= kinds


def test_budget_is_respected():
    p = generate_puzzle(40, seed=7)["grid"]
    res = hybrid_solver.solve(p, qubit_budget=10, use_singles=False, seed=2)
    _check(p, res)
    assert res["metrics"]["max_qubits"] <= 10


def test_solves_4x4_puzzle_with_grover():
    p = generate_puzzle(6, size=4, seed=3)["grid"]
    assert len(p) == 16
    res = hybrid_solver.solve(p, qubit_budget=8, use_singles=False, seed=1)
    _check(p, res)
    assert len(res["solution"]) == 16
    assert res["metrics"]["windows"] > 0
    kinds = {s["type"] for s in res["trace"]}
    assert {"window", "oracle", "diffusion", "measurement", "verification", "commit"} <= kinds

