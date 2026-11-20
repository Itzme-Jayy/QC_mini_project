"""Hybrid quantum-classical Sudoku solver.

A full 9x9 board cannot fit one Grover circuit on a classical simulator, so:
  propagate -> choose window -> Grover (oracle from constraints) -> verify -> commit -> repeat,
with depth-first backtracking when a window has no valid assignment or leads to a dead end.
No solutions are stored anywhere; every digit placed comes from propagation or a Grover
measurement that was verified against the Sudoku rules.
"""
import time

import numpy as np

from .encoding import decode_state, indices_to_digits
from .grover import WindowRunner
from .propagation import propagate
from .window import choose_window

DETAIL_WINDOWS = 12  # windows beyond this keep compact trace steps (no circuit/probabilities)


class _Frame:
    def __init__(self, base, cells, n_data):
        self.base, self.cells, self.n_data = base, cells, n_data
        self.queue, self.tried, self.exhausted = [], [], False


def solve(grid, *, qubit_budget=16, hard_cap=24, shots=64, max_attempts=10, max_windows=400,
          time_limit=180.0, use_singles=True, seed=None):
    t0 = time.perf_counter()
    rng = np.random.default_rng(seed)
    qubit_budget = min(qubit_budget, hard_cap)
    trace, stats = [], {"windows": 0, "grover_runs": 0, "iterations": 0, "backtracks": 0,
                        "max_qubits": 0, "simulations": 0}

    def add(kind, text, window_id=None, **payload):
        trace.append({"index": len(trace), "type": kind, "description": text, "window_id": window_id,
                      "payload": payload})

    def finish(status, solution=None, message=None):
        stats["time_ms"] = (time.perf_counter() - t0) * 1000
        return {"status": status, "solution": solution, "message": message, "metrics": stats, "trace": trace}

    def next_assignment(frame, wid, detailed):
        """Pop the next verified assignment for this window, calling Grover when the queue is empty."""
        if not frame.queue and not frame.exhausted:
            excluded = tuple(frame.tried) if len(frame.cells) and frame.tried else ()
            runner = WindowRunner(frame.cells, frame.n_data, excluded)
            if runner.n_total > qubit_budget:  # too many exclusion flags: filter classically instead
                runner = WindowRunner(frame.cells, frame.n_data, ())
            stats["grover_runs"] += 1
            stats["max_qubits"] = max(stats["max_qubits"], runner.n_total)
            res = runner.run(shots=shots, rng=rng, max_attempts=max_attempts)
            stats["iterations"] += res["total_iterations"]
            stats["simulations"] += len(res["attempts"])
            fresh = [decode_state(frame.cells, s) for s in res["found_states"]]
            fresh = [a for a in fresh if a not in frame.tried]
            cp = [c.pos for c in frame.cells]
            m = runner.metrics()
            if detailed:
                add("superposition",
                    f"Put the {frame.n_data} data qubits into uniform superposition with Hadamard gates: "
                    f"N = 2^{frame.n_data} = {runner.N} basis states, each with amplitude 1/sqrt(N).",
                    wid, window_cells=cp, n=frame.n_data, N=runner.N, circuit=runner.describe(res["total_iterations"]))
                add("oracle",
                    f"The oracle computes {len(runner.flags)} constraint flags (row/column/box conflicts, "
                    f"invalid indices{', previously tried assignments' if excluded else ''}), flips the phase when all flags are 0, "
                    f"then uncomputes the flags.", wid, window_cells=cp, flags=len(runner.flags), **m)
                add("diffusion",
                    "The diffusion operator reflects all amplitudes about their mean, boosting states the oracle marked.",
                    wid, window_cells=cp, depth=m["depth_per_iteration"])
                add("measurement",
                    f"BBHT search ran {len(res['attempts'])} attempt(s) with {res['total_iterations']} Grover "
                    f"iteration(s) in total and {shots} shots each.",
                    wid, window_cells=cp, attempts=res["attempts"], before=res["before"], after=res["after"],
                    success_probability=res["success_probability"], valid_count=res["valid_count"],
                    N=runner.N, iterations=res["shown_iterations"], optimal_iterations=res["optimal_iterations"],
                    note=res["note"])
            else:
                add("measurement", f"Grover run on {len(cp)} cells ({runner.n_total} qubits, "
                    f"{res['total_iterations']} iterations).", wid, window_cells=cp, N=runner.N)
            add("verification",
                f"Checked {len(res['found_states'])} measured outcome(s) against the Sudoku rules on a classical "
                f"computer: {len(fresh)} new valid assignment(s).", wid, window_cells=cp,
                valid=[indices_to_digits(frame.cells, a) for a in fresh])
            frame.queue = fresh
            if not fresh:
                frame.exhausted = True
        if frame.queue:
            a = frame.queue.pop(0)
            frame.tried.append(a)
            return a
        return None

    def apply(frame, assignment):
        g = list(frame.base)
        for c, i in zip(frame.cells, assignment):
            g[c.pos] = c.cands[i]
        return g

    state, stack, wid = list(grid), [], 0
    need_window = True
    while True:
        if time.perf_counter() - t0 > time_limit:
            return finish("timeout", message="Time limit reached before the puzzle was solved.")
        dead = False
        if need_window:
            state, cands, ok, assigned = propagate(state, use_singles)
            add("propagation",
                f"Constraint propagation filled {len(assigned)} cell(s) by naked/hidden singles; "
                f"{sum(1 for p in range(len(state)) if state[p] == 0)} cell(s) remain.",
                None, grid=state, assigned=assigned)
            if not ok:
                dead = True
                add("backtrack", "Propagation found a contradiction, so the last guess cannot be right.", None)
            elif all(state):
                add("result", "Every cell is filled and verified.", None, grid=state)
                return finish("solved", state)
            else:
                wid += 1
                if wid > max_windows:
                    return finish("unsolved", message="Window limit reached.")
                chosen = choose_window(cands, qubit_budget)
                if chosen is None:  # only forced cells (1 candidate) are left: fill them directly
                    state, _, ok2, forced = propagate(state, True)
                    add("propagation", f"Filled the {len(forced)} remaining forced cell(s).", None,
                        grid=state, assigned=forced)
                    if ok2:
                        continue
                    dead = True
                    add("backtrack", "Forced cells contradict each other.", None)
                else:
                    cells, n_data = chosen
                    stats["windows"] += 1
                    frame = _Frame(list(state), cells, n_data)
                    stack.append(frame)
                    detailed = wid <= DETAIL_WINDOWS
                    wcells = [c.pos for c in cells]
                    add("window",
                        f"Quantum window: {len(cells)} cell(s) using {n_data} data qubits (a cell with k "
                        f"candidates needs ceil(log2 k) qubits).", wid, window_cells=wcells, n=n_data,
                        candidates={str(c.pos): c.cands for c in cells})
                    a = next_assignment(frame, wid, detailed)
                    if a is None:
                        stack.pop()
                        dead = True
                        add("backtrack", "No valid assignment exists for this window in the current state.",
                            wid, window_cells=wcells)
                    else:
                        state = apply(frame, a)
                        add("commit", "Committed the verified assignment to the grid.", wid,
                            window_cells=wcells, grid=state)
                        continue
        if dead:
            resumed = False
            while stack:
                frame = stack[-1]
                stats["backtracks"] += 1
                a = next_assignment(frame, wid, False)
                if a is not None:
                    state = apply(frame, a)
                    add("commit", "Backtracked and tried the next valid assignment for this window.", wid,
                        window_cells=[c.pos for c in frame.cells], grid=state)
                    resumed = True
                    break
                stack.pop()
                add("backtrack", "Window exhausted; stepping back one level.", wid)
            if not resumed:
                return finish("unsolved", message="The search space was exhausted: this puzzle has no solution.")
        need_window = True
