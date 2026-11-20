"""Orchestrates solves and persists puzzles, runs and trace steps."""
import time

import numpy as np

from ..classical import backtracking
from ..extensions import db
from ..models import Puzzle, SolveRun, SolveStep
from ..quantum import hybrid_solver
from .generator import difficulty_for
from .validator import grid_to_str


def get_or_create_puzzle(grid):
    s = grid_to_str(grid)
    puzzle = Puzzle.query.filter_by(grid=s).first()
    if puzzle is None:
        size = int(len(grid) ** 0.5)
        puzzle = Puzzle(grid=s, difficulty=difficulty_for(sum(1 for v in grid if v), size=size))
        db.session.add(puzzle)
        db.session.flush()
    return puzzle


def _save(puzzle, method, status, solution, duration_ms, metrics, steps):
    run = SolveRun(
        puzzle_id=puzzle.id, method=method, status=status,
        solved_grid=grid_to_str(solution) if solution else None, duration_ms=duration_ms,
        qubits_used=metrics.get("max_qubits"), grover_iterations=metrics.get("iterations"),
        backtracks=metrics.get("backtracks"), nodes_explored=metrics.get("nodes"),
    )
    db.session.add(run)
    db.session.flush()
    for i, st in enumerate(steps):
        db.session.add(SolveStep(run_id=run.id, step_index=i, step_type=st["type"],
                                 description=st["description"],
                                 payload={**st.get("payload", {}), "window_id": st.get("window_id")}))
    db.session.commit()
    return run


def solve_quantum(grid, cfg, qubit_budget=None, shots=None, use_singles=True, seed=None):
    budget = max(cfg["MIN_QUBIT_BUDGET"], min(int(qubit_budget or cfg["DEFAULT_QUBIT_BUDGET"]), cfg["HARD_QUBIT_CAP"]))
    shots = max(1, min(int(shots or cfg["DEFAULT_SHOTS"]), 4096))
    puzzle = get_or_create_puzzle(grid)
    res = hybrid_solver.solve(
        grid, qubit_budget=budget, hard_cap=cfg["HARD_QUBIT_CAP"], shots=shots,
        max_attempts=cfg["MAX_GROVER_ATTEMPTS"], max_windows=cfg["MAX_WINDOWS"],
        time_limit=cfg["MAX_SOLVE_SECONDS"], use_singles=use_singles, seed=seed)
    run = _save(puzzle, "quantum", res["status"], res["solution"], res["metrics"]["time_ms"],
                res["metrics"], res["trace"])
    return {"run_id": run.id, "method": "quantum", "status": res["status"], "solution": res["solution"],
            "message": res["message"], "metrics": {**res["metrics"], "qubit_budget": budget, "shots": shots},
            "trace": [{"index": s["index"], "type": s["type"], "description": s["description"],
                       "payload": {**s["payload"], "window_id": s["window_id"]}} for s in res["trace"]]}


def solve_classical(grid):
    puzzle = get_or_create_puzzle(grid)
    res = backtracking.solve(grid, limit=1)
    sol = res["solutions"][0] if res["solutions"] else None
    metrics = {"nodes": res["nodes"], "backtracks": res["backtracks"], "time_ms": res["time_ms"]}
    run = _save(puzzle, "classical", "solved" if sol else "unsolved", sol, res["time_ms"], metrics, [])
    return {"run_id": run.id, "method": "classical", "status": "solved" if sol else "unsolved",
            "solution": sol, "metrics": metrics}


def is_solvable(grid):
    """Feasibility pre-check only; its answer is discarded and never reaches the quantum solver."""
    return backtracking.count_solutions(grid, limit=1) > 0
