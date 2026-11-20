from .solver_service import solve_classical, solve_quantum


def compare(grid, cfg, **quantum_opts):
    classical = solve_classical(grid)
    quantum = solve_quantum(grid, cfg, **quantum_opts)
    qt, ct = quantum["metrics"]["time_ms"], classical["metrics"]["time_ms"]
    return {
        "classical": classical, "quantum": quantum,
        "summary": {
            "slowdown": (qt / ct) if ct else None,
            "note": ("Qiskit Aer simulates every qubit on classical hardware, so each Grover iteration costs "
                     "time that grows as 2^n. The quantum speedup (about sqrt(N) instead of N) only appears "
                     "on real quantum hardware, so the simulator is expected to be slower here."),
        },
    }
