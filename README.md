# Quantum Sudoku Solver

A general-purpose 9×9 Sudoku solver that uses Grover's algorithm with a constraint-based
oracle, plus a web interface that shows what the quantum part is doing. Everything runs on a
**local Qiskit Aer simulator**; no IBM account, cloud backend or API key is needed.

Stack: React + Vite + Tailwind CSS · Flask · Qiskit + Qiskit Aer · PostgreSQL.

## Why the solver is hybrid

A full board cannot be a single Grover circuit on a classical simulator: 81 cells at 4 bits
each is hundreds of qubits, and statevector simulation stops around 25–30 qubits. So the
solver works in small *windows*:

1. **Propagate.** Classical naked/hidden singles shrink every cell's candidate list.
2. **Choose a window.** Take the most constrained empty cell, then greedily add interacting
   peer cells while *data qubits + ancilla flags* stay within the qubit budget
   (default 16, hard cap 24).
3. **Grover search.** A cell with k candidates uses ⌈log₂ k⌉ qubits. The oracle is built from
   the Sudoku rules (see below), the diffusion operator amplifies the marked states, and the
   BBHT strategy picks iteration counts because the number of solutions is unknown.
4. **Verify and commit.** Each measured outcome is checked against the Sudoku rules on a
   classical computer, then committed to the grid. Return to step 1.
5. **Backtrack.** If a window has no valid assignment or leads to a contradiction, the
   solver tries the next verified assignment (previously tried ones are excluded in the
   oracle, or filtered classically when there is no qubit budget left) and otherwise steps
   back a level. This keeps the search complete for any valid puzzle.

Honest limits: the simulator makes the quantum path slower than plain backtracking
(each added qubit doubles simulation cost; a real quantum speedup is not reproduced on a
classical machine). "No solution in this window" is decided by BBHT with a bounded number of
attempts, so it is probabilistic: it can wrongly report a window as empty with small
probability. BBHT is varied slightly so every run uses at least one Grover iteration.

### The oracle

Built generically from constraints, never from a stored answer:

* **Conflict flags** – for every pair of window cells sharing a row/column/box and every
  digit both can hold, a multi-controlled X sets an ancilla when both hold that digit.
* **Invalid-index flags** – basis states that do not name a candidate (index ≥ k) are
  covered by a few aligned blocks, each flagged by one gate.
* **Excluded flags** – assignments that were tried and led to a dead end.
* The oracle flips the phase when **all flags are 0**, then uncomputes the flags so every
  ancilla returns to |0⟩. Conflicts with given cells are handled by candidate filtering.

## Architecture

```
React (Vite, Tailwind) ──REST──▶ Flask routes ──▶ services ──▶ quantum / classical packages
                                                      └──────▶ PostgreSQL (puzzles, runs, steps)
```

`app/quantum` and `app/classical` have no Flask imports and can be tested on their own.
Every quantum solve returns a structured trace (propagation, window, superposition, oracle,
diffusion, measurement, verification, commit/backtrack) that the UI replays.

## Folder structure

```
quantum-sudoku/
  docker-compose.yml        PostgreSQL 16
  .env.example              copy to backend/.env
  backend/
    run.py  requirements.txt  conftest.py
    app/
      __init__.py (factory)  config.py  extensions.py  models.py
      core/geometry.py       rows, columns, boxes, peers
      routes/                health.py  puzzles.py  solve.py
      services/              solver_service  comparison_service  generator  validator
      quantum/               encoding  propagation  window  oracle  diffusion
                             grover  circuit_export  hybrid_solver
      classical/backtracking.py
    migrations/              Alembic (Flask-Migrate) initial schema
    tests/                   pytest suite
  frontend/
    package.json  vite.config.js  tailwind.config.js  postcss.config.js
    src/
      App.jsx  main.jsx  index.css
      api/client.js  context/ThemeContext.jsx  hooks/useSolver.js  utils/sudoku.js
      components/            SudokuGrid Controls ComparisonPanel CircuitView
                             ProbabilityChart StepExplainer ThemeToggle PuzzleHistory
      tests/                 Vitest + React Testing Library
```

## Database

* `puzzles` (id, grid – 81-char string of givens, difficulty, created_at)
* `solve_runs` (id, puzzle_id, method, status, solved_grid, duration_ms, qubits_used,
  grover_iterations, backtracks, nodes_explored, created_at)
* `solve_steps` (id, run_id, step_index, step_type, description, payload JSON)

## API

| Method | Path | Purpose |
|---|---|---|
| GET | /api/health | liveness |
| POST | /api/puzzles/validate | `{grid}` → conflicts |
| POST | /api/puzzles/generate | `{clues, seed?}` → random unique puzzle |
| POST | /api/solve/quantum | `{grid, qubit_budget?, shots?, propagation?}` → solution + trace |
| POST | /api/solve/classical | `{grid}` |
| POST | /api/solve/compare | both, with side-by-side metrics |
| GET | /api/runs, /api/runs/<id> | history and full trace |

`grid` is 81 integers (0 = empty), a 9×9 nested list, or an 81-character string. Bad input
returns 400 with a message; a puzzle with no solution returns 422. The no-solution check
uses the classical solver purely as a feasibility gate; its answer is discarded.

## Setup

Prerequisites: Python 3.11+, Node 18+, Docker.

```bash
# 1. database
docker compose up -d

# 2. backend
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
export FLASK_APP=run.py                                 # Windows: set FLASK_APP=run.py
flask db upgrade
python run.py                                           # http://localhost:5001 (port 5001 avoids macOS AirPlay on 5000)

# 3. frontend (new terminal)
cd frontend
npm install
npm run dev                                             # http://localhost:5173 (proxies /api)
```

## Tests

```bash
cd backend && pytest            # validator, propagation, oracle truth table, Grover, hybrid solver, API, no-hardcoded scan
cd frontend && npm test         # grid input, conflicts, theme persistence, chart/stepper/circuit
```

Backend API tests use an in-memory SQLite database. The oracle test compares the phase
pattern from a statevector against brute-force enumeration of the window; the solver tests
check results by Sudoku rules and given-preservation, never against stored answers.

## No hardcoded solutions

There are no solved grids, answer strings or lookup tables in the source. Puzzles come from
user input or the runtime generator (randomized backtracking, then cell removal while the
solution stays unique). `tests/test_no_hardcoded_solutions.py` scans the solver, service and
route packages and fails on any 81-digit literal or 81-item integer list.

## Troubleshooting

* **Aer fails to install** – use Python 3.9–3.13 and upgrade pip first
  (`pip install -U pip`). On Apple Silicon or Alpine, prefer a recent Python from
  python.org/conda. Pinned versions: qiskit 2.6.2, qiskit-aer 0.18.4.
* **Out of memory or very slow solves** – a statevector needs 16·2ⁿ bytes (24 qubits ≈ 270 MB).
  Lower the *Qubit budget* in the UI (try 12–14) or set `QUBIT_BUDGET` in `.env`.
  Time limit: `MAX_SOLVE_SECONDS`.
* **CORS errors** – set `CORS_ORIGINS` to the exact frontend origin, or use the Vite proxy
  (the default `/api` base URL).
* **Database connection errors** – check `docker compose ps`, that port 5432 is free, and
  that `DATABASE_URL` in `backend/.env` matches `docker-compose.yml`. Run `flask db upgrade`
  before the first request. History shows "unavailable" if the DB is down; solving still fails
  without it because every run is saved.
* **Proxy timeouts on long solves** – the Vite proxy has no timeout; if you front the API
  with another proxy, raise its read timeout.
