# Quantum Sudoku Solver - Comprehensive Technical Project Documentation

> A hybrid quantum-classical Sudoku solving engine and interactive visualizer powered by **Qiskit Aer**, **Flask**, **React**, and **PostgreSQL**. Demonstrates real-world quantum constraint satisfaction through dynamic windowing, Grover's search algorithm, constraint-based phase kickback oracles, and amplitude amplification.

---

## 1. Executive Summary & Problem Formulation

### 1.1 The Computational Challenge: Sudoku as NP-Complete CSP
Sudoku is a canonical Constraint Satisfaction Problem (CSP) and an instance of the Exact Cover problem, proven to be NP-complete for generalized $N \times N$ boards ($N = n^2$). The objective is to assign digits $d \in \{1, \dots, N\}$ to empty cells in an $N \times N$ grid such that each digit appears exactly once in every row, column, and $\sqrt{N} \times \sqrt{N}$ subgrid box.

On a standard 9×9 board:
- There are 81 cells, each requiring a 4-bit binary representation ($\lceil \log_2 9 \rceil = 4$).
- A naive, monolithic quantum representation would demand:
  $$81 \times 4 = 324 \text{ data qubits}$$
- The state space has dimension $2^{324} \approx 2 \times 10^{97}$ orthogonal basis states.
- On modern quantum simulators, exact statevector simulation scales as $\mathcal{O}(2^n)$ in memory (storing $2^n$ complex numbers). A 30-qubit statevector requires $16 \text{ GB}$ of RAM; 324 qubits is astronomically beyond all computational hardware in existence.

### 1.2 The Hybrid Quantum-Classical Paradigm
To solve arbitrary Sudoku puzzles on local quantum hardware or simulators without compromising quantum rigor, this project implements a **Hybrid Quantum-Classical Windowing Engine**:
1. **Classical Deduction**: Prunes search space using deterministic constraint propagation (naked and hidden singles).
2. **Window Partitioning**: Identifies tightly coupled, high-conflict clusters of 2–4 unassigned cells whose data and ancilla qubit requirements fit strictly within a predefined `qubit_budget` (typically 8–16 qubits, hard cap 24).
3. **Grover's Amplitude Amplification**: Constructs and executes a parameterized quantum circuit using Qiskit Aer that evaluates Sudoku peer constraints via quantum phase kickback, amplifying valid candidate assignments while suppressing invalid ones.
4. **Classical Verification & DFS Backtracking**: Measures candidate bitstrings, verifies them classically against the global grid rules, and commits or backtracks using a stack of quantum execution frames.

---

## 2. System Architecture & Tech Stack

```mermaid
flowchart TD
    subgraph Frontend["Frontend Client (React 18 + Vite + Tailwind CSS)"]
        UI["Sudoku Interactive Grid (4×4 & 9×9)"]
        Ctrl["Controls & Keypad (1–4 / 1–9)"]
        Explainer["Step-by-Step Algorithm Replay"]
        Circuit["Circuit Visualizer (Wire & Gate Layers)"]
        ProbChart["Measurement Probability Chart (Recharts)"]
        History["Puzzle History & Benchmarks"]
    end

    subgraph Backend["Backend Application (Flask Application Factory)"]
        API["REST API Router (/api/puzzles, /api/solve, /api/runs)"]
        Validator["Grid Validator & Conflict Detector"]
        Generator["Algorithmic Puzzle Generator (4×4 & 9×9)"]
        Classical["Classical Backtracking Solver (Bitmask Optimization)"]
        Hybrid["Hybrid Quantum Solver Engine"]
    end

    subgraph Quantum["Quantum Execution Layer (Qiskit 1.x + Qiskit Aer)"]
        Geometry["Board Geometry (size 4 / 9, 2×2 / 3×3 boxes, peers)"]
        Window["Greedy Window Selection Heuristic"]
        Encoding["Qubit Register Allocator (⌈log₂ k⌉ per cell)"]
        Oracle["Constraint Oracle (Phase Kickback & Uncomputation)"]
        Diffusion["Grover Diffusion Operator (Reflection about Mean)"]
        Simulator["AerSimulator (statevector method, local)"]
    end

    subgraph Database["Storage Layer (PostgreSQL 16 in Docker)"]
        DB[(PostgreSQL 16)]
        PuzzlesTbl["puzzles table (givens, difficulty, size)"]
        RunsTbl["solve_runs table (qubits, iterations, duration)"]
        StepsTbl["solve_steps table (JSON execution trace)"]
    end

    UI --> API
    Ctrl --> API
    API --> Validator
    API --> Generator
    API --> Classical
    API --> Hybrid
    Hybrid --> Geometry
    Hybrid --> Window
    Hybrid --> Encoding
    Hybrid --> Oracle
    Hybrid --> Diffusion
    Diffusion --> Simulator
    API --> DB
    DB --> History
    Hybrid -.->|Structured Trace| Explainer
    Encoding -.->|Circuit Layout| Circuit
    Simulator -.->|Pre/Post Probabilities| ProbChart
```

### Technology Breakdown

| Component | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | React | `^18.3.1` | Declarative reactive UI components, hook-based solver state. |
| **Build & Bundler** | Vite | `^5.4.11` | Ultra-fast HMR, reverse proxy routing for API calls. |
| **Styling** | Tailwind CSS | `^3.4.15` | Responsive dark/light theme styling, dynamic grid layouts. |
| **Charting** | Recharts | `^2.13.3` | Side-by-side quantum measurement probability distribution plots. |
| **Icons** | Lucide React | `^0.460.0` | Accessible iconography for controls, playback, and navigation. |
| **Backend Framework** | Flask | `~3.1.0` | Application factory pattern, RESTful endpoints, CORS management. |
| **ORM & Migrations** | Flask-SQLAlchemy, Flask-Migrate | `~3.1.1`, `~4.0.7` | PostgreSQL relational persistence and Alembic schema migrations. |
| **Quantum Framework** | Qiskit | `~1.3.0` | Quantum circuit composition, gate transpilation, and measurement. |
| **Quantum Simulation** | Qiskit Aer | `~0.15.1` | Local high-performance statevector simulator (`save_probabilities`). |
| **Numerical Computing**| NumPy | `~2.2.0` | Probability tensor calculations, bit manipulation, and RNG. |
| **Database** | PostgreSQL | `16-alpine` | Relational storage for puzzle states, execution metrics, and step traces. |
| **Containerization** | Docker & Compose | Compose v2 | Isolated PostgreSQL container mapped to host port 5433. |
| **Testing** | Pytest, Vitest | `9.2.0`, `2.1.8` | 33 backend tests and 13 frontend tests ensuring zero regressions. |

---

## 3. What Is Done (Functional Capabilities)

### 3.1 Dual Board Size Architecture: 4×4 (Mini) & 9×9 (Standard)
- **Standard 9×9 Mode**: 81 cells, 9 rows, 9 columns, nine 3×3 subgrid boxes, digits 1–9, 20 peers per cell. Ideal for observing real hybrid windowing and backtracking.
- **Mini 4×4 Mode**: 16 cells, 4 rows, 4 columns, four 2×2 subgrid boxes, digits 1–4, 7 peers per cell. Each cell has at most 4 candidates, needing strictly 2 data qubits ($\lceil \log_2 4 \rceil = 2$). A 2-cell window needs only 4 data qubits ($N = 16$ basis states), allowing complete visual enumeration of the entire Hilbert space.
- Seamless toggling between 4×4 and 9×9 in the UI with dynamic keypad adaptation (keys 1–4 vs 1–9), arrow key bounds checking, and dynamic border rendering.

### 3.2 Pure Algorithmic Integrity (Zero Hardcoded Answers)
- Enforced by regression tests (`test_no_hardcoded_solutions.py`), no 16-element or 81-element solution strings exist in the repository.
- Puzzles are generated algorithmically using randomized seed-driven backtracking with minimal clue carving, and every solved digit is computed through quantum simulation or logical deduction.

### 3.3 Dynamic Quantum Circuit Visualizer
- Exports the exact OpenQASM-style gate pipeline for any active window:
  - Superposition layer ($H$).
  - Oracle constraint comparator blocks ($X$, $CX$, $MCX$).
  - Phase kickback flag verification.
  - Grover diffusion reflection gates.
  - Classical measurement registers.

### 3.4 Live Measurement Probability Visualization
- Shows side-by-side probability bars for every basis state $|x\rangle$:
  - **Before Amplification**: Flat uniform distribution $P(x) = \frac{1}{N}$.
  - **After Grover Amplification**: Valid states spiked to high probability ($>80\%$), invalid configurations suppressed to near zero.

### 3.5 Step-by-Step Algorithm Walkthrough
- Recorded trace playback with automated timeline slider and Play/Pause controls.
- Dynamically rendered mathematical formulas explaining:
  - Candidate subtraction: $\text{cands}(c) = \{1\dots N\} \setminus \text{peers}(c)$.
  - Superposition: $|\psi_0\rangle = H^{\otimes n}|0\dots 0\rangle = \frac{1}{\sqrt{N}}\sum |x\rangle$.
  - Phase inversion: $O|x\rangle = (-1)^{f(x)}|x\rangle$.
  - Diffusion: $D = 2|s\rangle\langle s| - I$.
  - Success probability: $P(\text{success}) = \sin^2((2k+1)\theta)$.

### 3.6 Comparative Classical vs Quantum Benchmarking
- Single-click **"Compare both"** execution:
  - Runs the optimized classical bitmask backtracking solver.
  - Runs the hybrid quantum Aer simulator solver.
  - Displays side-by-side metrics: Wall-clock time (ms), nodes explored vs Grover runs, quantum circuit iterations, and backtracks.

---

## 4. What Is Used (Mathematical & Quantum Formulations)

### 4.1 Quantum State Encoding
Let a selected window consist of $m$ cells $\{c_1, c_2, \dots, c_m\}$. Each cell $c_i$ has a candidate set $\mathcal{C}_i \subseteq \{1, \dots, S\}$ where $k_i = |\mathcal{C}_i|$.
- Number of data qubits allocated to cell $c_i$:
  $$q_i = \lceil \log_2 k_i \rceil$$
- Total data qubits in the window register:
  $$n = \sum_{i=1}^m q_i$$
- Total Hilbert space dimension:
  $$N = 2^n$$
- Mapping: Each integer basis state $x \in \{0, \dots, N-1\}$ is decoded into cell candidate indices $(idx_1, \dots, idx_m)$ using bit-slicing:
  $$idx_i = (x \gg \text{shift}_i) \ \& \ (2^{q_i} - 1)$$
- If $idx_i < k_i$, the assigned digit is the $idx_i$-th sorted candidate of $c_i$. If $idx_i \ge k_i$, the assignment is an **out-of-range invalid index**.

### 4.2 Uniform Superposition State
Applying the Hadamard transform $H^{\otimes n}$ to the initialized ground state $|0\dots 0\rangle$ produces an equal superposition:
$$|\psi_0\rangle = H^{\otimes n} |0\dots 0\rangle = \frac{1}{\sqrt{N}} \sum_{x=0}^{N-1} |x\rangle$$

### 4.3 Constraint Oracle ($O$) Formulation
The oracle is a Boolean phase oracle operating on the computational basis:
$$O |x\rangle = (-1)^{f(x)} |x\rangle$$
where $f(x) \in \{0, 1\}$ is 1 if and only if assignment $x$ satisfies all three constraint classes:
1. **Valid Range Constraint**: For each cell $c_i$, $idx_i < k_i$. Out-of-bounds indices are detected by bitmask flags.
2. **Peer Uniqueness Constraint**: For any pair $(c_i, c_j)$ that are peers (sharing a row, column, or box) and share candidate digit $d \in \mathcal{C}_i \cap \mathcal{C}_j$:
   $$\text{assign}(c_i) \neq \text{assign}(c_j)$$
   Multi-controlled Toffoli ($MCX$) gates set an ancilla conflict flag $|a_{\text{conflict}}\rangle = |1\rangle$ if both cells decode to digit $d$.
3. **Exclusion Constraint**: Assignments that were previously tested in this window and led to a dead-end branch in downstream propagation are explicitly flagged.

#### Phase Kickback Mechanism
An ancilla qubit is prepared in the $|-\rangle$ state:
$$|-\rangle = \frac{|0\rangle - |1\rangle}{\sqrt{2}}$$
When all conflict flags are zero (indicating no constraint violations), an $X$ gate targets the phase ancilla:
$$X |-\rangle = \frac{|1\rangle - |0\rangle}{\sqrt{2}} = -|-\rangle$$
This kicks the negative eigenvalue $-1$ back onto the state $|x\rangle$.
Finally, **uncomputation** is applied: all comparator gates are executed in reverse order, returning every ancilla flag to $|0\rangle$ and decoupling them from the data register to preserve quantum coherence.

### 4.4 Grover Diffusion Operator ($D$)
The diffusion operator reflects quantum state vectors across their mean amplitude:
$$D = 2 |\psi_0\rangle \langle \psi_0| - I$$
Implemented through elementary gates:
$$D = H^{\otimes n} \left( 2 |0\dots 0\rangle \langle 0\dots 0| - I \right) H^{\otimes n} = H^{\otimes n} X^{\otimes n} \left( MCZ \right) X^{\otimes n} H^{\otimes n}$$
where $MCZ$ is a multi-controlled $Z$ gate implemented via multi-controlled Toffoli sandwiched between single-qubit Hadamards on the target qubit.

### 4.5 Geometric Amplitude Amplification & Success Probability
Grover's algorithm operates within a 2-dimensional plane spanned by:
- $|\alpha\rangle$: the normalized superposition of non-solution states ($N - M$ states).
- $|\beta\rangle$: the normalized superposition of valid marked states ($M$ states).

The initial superposition can be expressed as:
$$|\psi_0\rangle = \cos\theta |\alpha\rangle + \sin\theta |\beta\rangle, \quad \text{where } \sin\theta = \sqrt{\frac{M}{N}}$$

Each Grover iteration $G = D \cdot O$ rotates the state vector by angle $2\theta$ toward $|\beta\rangle$. After $k$ iterations:
$$G^k |\psi_0\rangle = \cos((2k+1)\theta) |\alpha\rangle + \sin((2k+1)\theta) |\beta\rangle$$

The probability of measuring a valid solution state is:
$$P(\text{success} \mid k) = \sin^2((2k+1)\theta) = \sin^2\left((2k+1)\arcsin\sqrt{\frac{M}{N}}\right)$$

The optimal iteration count maximizing $P(\text{success})$ is:
$$k_{\text{opt}} \approx \left\lfloor \frac{\pi}{4} \sqrt{\frac{N}{M}} \right\rfloor$$

### 4.6 Boyer-Brassard-Høyer-Tapp (BBHT) Adaptive Search
Because the number of valid solutions $M$ in an arbitrary Sudoku window is unknown in advance, fixed-iteration Grover search could over-rotate and miss solutions. The engine uses the **BBHT algorithm**:
1. Initialize iteration parameter bound $m = 1.0$, scaling factor $\lambda = \frac{6}{5} = 1.2$.
2. For each attempt, randomly choose iteration count $j \in [1, \lfloor m \rfloor]$.
3. Execute the Grover circuit $(D \cdot O)^j$ on Qiskit Aer and sample 64 shots.
4. If a measured state satisfies classical verification, terminate and return the solution.
5. If no valid assignment is found, update the bound $m \leftarrow \min(\lambda m, \sqrt{N})$ and repeat up to `max_attempts`.

---

## 5. How It Is Done (Implementation Deep-Dive)

### 5.1 Project Directory Structure

```
quantum-sudoku/
├── docker-compose.yml              # PostgreSQL 16 service definition
├── .env.example                    # Template environment variables
├── README.md                       # High-level overview
├── DOCUMENTATION.md                # Exhaustive technical documentation (this file)
├── backend/
│   ├── run.py                      # Flask entry point (port 5001)
│   ├── requirements.txt            # Python dependencies (qiskit, flask, psycopg2, etc.)
│   ├── conftest.py                 # Pytest configuration
│   ├── app/
│   │   ├── __init__.py             # Flask application factory
│   │   ├── config.py               # Dotenv loading (override=True) & DB URI
│   │   ├── extensions.py           # SQLAlchemy & Migrate singletons
│   │   ├── models.py               # Puzzle, SolveRun, SolveStep relational schemas
│   │   ├── core/
│   │   │   └── geometry.py         # BoardGeometry (4x4 and 9x9 units, rows, cols, peers)
│   │   ├── routes/
│   │   │   ├── health.py           # Liveness probe & simulator status
│   │   │   ├── puzzles.py          # /api/puzzles/generate & /api/puzzles/validate
│   │   │   ├── solve.py            # /api/solve/quantum, /classical, /compare
│   │   │   └── runs.py             # /api/runs (history listing & detail retrieval)
│   │   ├── services/
│   │   │   ├── generator.py        # Seedable puzzle generator with difficulty scoring
│   │   │   ├── validator.py        # Grid parser, conflict detector, rule verifier
│   │   │   ├── solver_service.py   # Hybrid solve dispatcher & DB persistence
│   │   │   └── comparison_service.py # Side-by-side run comparison builder
│   │   ├── classical/
│   │   │   └── backtracking.py     # High-speed bitmask backtracking solver
│   │   └── quantum/
│   │       ├── encoding.py         # WindowCell dataclass, bit-decoding utilities
│   │       ├── propagation.py      # Naked & hidden singles deductive engine
│   │       ├── window.py           # Greedy heuristic window partitioner
│   │       ├── oracle.py           # Dynamic Qiskit circuit oracle builder
│   │       ├── diffusion.py        # Qiskit Grover diffusion reflection operator
│   │       ├── circuit_export.py   # JSON serializable circuit layout exporter
│   │       ├── grover.py           # WindowRunner (BBHT loop, Aer simulator runner)
│   │       └── hybrid_solver.py    # Main iterative hybrid loop with frame stack
│   ├── migrations/                 # Alembic migration scripts
│   └── tests/                      # 33 unit and integration tests
└── frontend/
    ├── package.json                # React, Vite, Tailwind, Recharts dependencies
    ├── vite.config.js              # Vite server setup with reverse proxy to port 5001
    ├── tailwind.config.js          # Tailwind theme colors and responsive breakpoints
    ├── postcss.config.js           # PostCSS Tailwind preprocessor
    └── src/
        ├── App.jsx                 # Top-level application container
        ├── main.jsx                # DOM mount & theme provider initialization
        ├── index.css               # Global typography, color variables, button styles
        ├── api/
        │   └── client.js           # Fetch wrapper for all backend REST endpoints
        ├── context/
        │   └── ThemeContext.jsx    # Dark/light theme state and local persistence
        ├── hooks/
        │   └── useSolver.js        # Core reactive hook managing grid, options, solve state
        ├── utils/
        │   └── sudoku.js           # Client-side validation, conflict finding, coordinates
        ├── components/
        │   ├── SudokuGrid.jsx      # Responsive 4x4 & 9x9 grid with border accents
        │   ├── Controls.jsx        # Board size toggle, keypad, actions, options
        │   ├── ComparisonPanel.jsx # Side-by-side metric comparison cards
        │   ├── CircuitView.jsx     # Visual gate and wire layout renderer
        │   ├── ProbabilityChart.jsx# Bar chart showing before/after Grover probabilities
        │   ├── StepExplainer.jsx   # Trace playback timeline with mathematical notes
        │   ├── ThemeToggle.jsx     # Accessible theme switch button
        │   └── PuzzleHistory.jsx   # Past runs drawer with reload capability
        └── tests/                  # 13 Vitest + React Testing Library suites
```

---

### 5.2 Step-by-Step Code Flow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Frontend (React)
    participant API as Flask REST API
    participant Hybrid as HybridSolver
    participant Classical as Propagation Engine
    participant Qiskit as Qiskit Aer Simulator
    participant DB as PostgreSQL Database

    User->>UI: Select 4×4, Click "Solve with quantum"
    UI->>API: POST /api/solve/quantum {grid: [16], qubit_budget: 8}
    API->>API: validator.parse_grid() & find_conflicts()
    API->>Hybrid: hybrid_solver.solve(grid, qubit_budget=8)
    
    loop While Unsolved
        Hybrid->>Classical: propagate(grid, use_singles=True)
        Classical-->>Hybrid: filled_cells, remaining_candidates
        
        alt All cells filled
            Hybrid->>Hybrid: Verify complete grid
        else Cells remain
            Hybrid->>Hybrid: choose_window(candidates, budget=8)
            Hybrid->>Qiskit: Build superposition (H), Oracle (O), Diffusion (D)
            Hybrid->>Qiskit: Run Aer statevector simulation (BBHT j iterations)
            Qiskit-->>Hybrid: Sampled counts & measured basis states
            Hybrid->>Classical: Verify top states against local rules
            alt Valid state found
                Hybrid->>Hybrid: Commit assignment to grid state
            else Dead end
                Hybrid->>Hybrid: Pop frame stack & backtrack
            end
        end
    end
    
    Hybrid-->>API: Return {status: "solved", solution, metrics, trace}
    API->>DB: INSERT into solve_runs, solve_steps
    API-->>UI: JSON response
    UI-->>User: Render solution, circuit view, and probability chart
```

---

### 5.3 Detailed Component Logic

#### 1. Geometry Module (`backend/app/core/geometry.py`)
Encapsulates all board topological constraints without any global hardcoding:
```python
class BoardGeometry:
    def __init__(self, size: int):
        self.size = size
        self.box_size = int(size ** 0.5)
        self.num_cells = size * size
        # Precomputes ROWS, COLS, BOXES, UNITS, and PEERS
```
- For size 9: 81 cells, $3 \times 3$ boxes, 20 peers per cell.
- For size 4: 16 cells, $2 \times 2$ boxes, 7 peers per cell.

#### 2. Classical Propagation (`backend/app/quantum/propagation.py`)
Computes candidate sets for all empty cells by intersecting negative bitmasks of row, column, and box peers.
- **Naked Singles**: $|\text{candidates}(c)| = 1 \implies$ digit placed immediately.
- **Hidden Singles**: A digit appears in only one empty cell within a unit $\implies$ digit placed immediately.
- Repeats iteratively until no further single-cell deductions can be made.

#### 3. Greedy Window Selection (`backend/app/quantum/window.py`)
Selects the subproblem for quantum execution:
1. Picks the empty cell with the smallest candidate count (most constrained).
2. Greedily adds peer cells that share constraints with already selected cells.
3. Stops when adding another cell would exceed `qubit_budget`:
   $$\sum_{c \in \text{window}} \lceil \log_2 k_c \rceil + \text{ancillae} > \text{budget}$$

#### 4. Dynamic Oracle Construction (`backend/app/quantum/oracle.py`)
Constructs the quantum phase oracle circuit:
- Allocates comparator ancilla qubits for every conflicting pair of window cells.
- Encodes candidate indices using $X$ (NOT) gates to represent binary zeros.
- Employs `mcx` (multi-controlled NOT) targeting conflict ancillae.
- Uses a multi-controlled gate targeting the phase ancilla in state $|-\rangle$.
- Inverts all comparator gates to return ancillae to $|0\rangle$.

#### 5. Grover Simulation & BBHT Execution (`backend/app/quantum/grover.py`)
Manages quantum execution through `WindowRunner`:
- Transpiles the quantum circuit against the local Aer statevector simulator.
- Calls `qc.save_probabilities(data_qubits)` to extract true probability amplitudes prior to measurement.
- Samples 64 measurement shots.
- Evaluates success metrics and dynamically adapts the iteration bound $m \leftarrow \min(1.2m, \sqrt{N})$.

#### 6. Database Storage & REST Endpoints
- `POST /api/puzzles/generate`: Algorithmic puzzle generation (`size=4|9`, `clues=N`).
- `POST /api/puzzles/validate`: Checks row/column/box conflicts and rejects invalid givens.
- `POST /api/solve/quantum`: Executes hybrid solver, writes metrics and full trace to PostgreSQL.
- `POST /api/solve/classical`: Runs classical bitmask backtracker for baseline comparison.
- `POST /api/solve/compare`: Executes both solvers concurrently on the same puzzle and computes comparative deltas.
- `GET /api/runs`: Returns paginated history of all past quantum and classical runs.
- `GET /api/runs/<id>`: Returns the complete step-by-step trace and circuit payloads for replay.

---

## 6. Verification, Testing & Bug Fixes

### 6.1 Architectural Hardening & Bug Fix Log

1. **macOS Port 5000 AirPlay Conflict**:
   - *Problem*: On macOS Monterey and later, Apple's AirPlay Receiver daemon binds to port 5000 by default. Vite proxy calls to `localhost:5000` failed with connection refused.
   - *Resolution*: Moved Flask backend to port 5001 (`backend/run.py`), updated Vite dev server proxy target in [`frontend/vite.config.js`](file:///Users/jay/projects/quantum-sudoku/frontend/vite.config.js#L8).

2. **Uninitialized PostgreSQL Tables**:
   - *Problem*: Docker container was active on port 5433, but API calls returned 500 Internal Server Error due to missing relational tables.
   - *Resolution*: Executed `flask db upgrade`, running initial Alembic migrations to construct `puzzles`, `solve_runs`, and `solve_steps`.

3. **Stale Environment Variables in Subprocesses**:
   - *Problem*: Running processes attempted connecting to default port 5432 instead of 5433 because `load_dotenv()` did not override inherited shell variables.
   - *Resolution*: Configured `load_dotenv(find_dotenv(), override=True)` in [`backend/app/config.py`](file:///Users/jay/projects/quantum-sudoku/backend/app/config.py).

4. **Node 22 Vitest `localStorage` Incompatibility**:
   - *Problem*: Node 22 defines an uninitialized global `localStorage` property when executed without `--localstorage-file`, crashing jsdom cleanup during test runs.
   - *Resolution*: Injected a mock storage polyfill in [`frontend/src/tests/setup.js`](file:///Users/jay/projects/quantum-sudoku/frontend/src/tests/setup.js).

5. **IndexError on 4×4 Board Solves**:
   - *Problem*: Hardcoded `range(81)` in `backend/app/quantum/hybrid_solver.py` threw `IndexError` when counting remaining cells on 16-cell grids.
   - *Resolution*: Replaced with `range(len(state))` for dynamic board dimension support.

### 6.2 Test Suite Verification

#### Backend Tests (33 tests passed)
```bash
cd backend && .venv/bin/pytest -v
```
- `test_api.py`: Validates health probe, conflict validator, 4×4 generation, classical solve, quantum solve, run detail retrieval, and 422 error rejection on unsolvable puzzles.
- `test_classical.py`: Tests bitmask backtracking solver and solution counter across valid and invalid puzzles.
- `test_grover.py`: Tests window quantum circuit synthesis, phase kickback, and diffusion operations.
- `test_hybrid_solver.py`: Tests end-to-end quantum solving with propagation, Grover window execution without singles, budget adherence, and 4×4 mini-Sudoku solving.
- `test_no_hardcoded_solutions.py`: Enforces zero hardcoded 16- or 81-character answer literals across the entire backend codebase.
- `test_oracle.py`: Tests conflict pair detection, invalid index bitmask generation, and phase inversion logic.
- `test_propagation.py`: Tests naked singles, hidden singles, and empty grid deduction.
- `test_validator.py`: Tests grid parsing, coordinate mapping, and completeness verification.

#### Frontend Tests (13 tests passed)
```bash
cd frontend && npm test -- --run
```
- `sudoku.test.js`: Tests row, column, and 2×2 / 3×3 box conflict detection for both 4×4 and 9×9 grids.
- `SudokuGrid.test.jsx`: Tests cell selection, keyboard number entry/deletion, arrow key navigation bounds, conflict highlighting, and 4×4 grid layout rendering.
- `ThemeToggle.test.jsx`: Tests dark/light theme switching and local storage persistence.
- `trace.test.jsx`: Tests step-by-step algorithm playback, gate display in circuit viewer, and probability chart bar rendering.

---

## 7. Setup & Execution Guide

### 7.1 Prerequisites
- **Python**: 3.11+ (Python 3.13 recommended)
- **Node.js**: 18+ (Node 20 or 22)
- **Docker & Docker Compose**: For local PostgreSQL database

### 7.2 Environment Configuration
Copy `.env.example` to `backend/.env`:
```bash
cp .env.example backend/.env
```
Ensure `backend/.env` contains:
```ini
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=dev-secret-key
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/quantum_sudoku
QUBIT_BUDGET=16
MAX_QUBIT_HARD_CAP=24
DEFAULT_SHOTS=64
```

### 7.3 Start PostgreSQL Service
```bash
docker compose up -d
```
Verify container status:
```bash
docker ps --filter "name=quantum-sudoku-db-1"
```

### 7.4 Backend Setup & Migrations
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask db upgrade
python run.py
```
*The backend server will start on `http://127.0.0.1:5001`.*

### 7.5 Frontend Setup & Execution
```bash
cd frontend
npm install
npm run dev
```
*The frontend interface will open on `http://localhost:5173`.*

---

## 8. Summary of Key Files

| File Path | Description |
| :--- | :--- |
| [`backend/app/core/geometry.py`](file:///Users/jay/projects/quantum-sudoku/backend/app/core/geometry.py) | Dynamic board geometry (size 4 / 9, box dimensions, peer lookups). |
| [`backend/app/quantum/oracle.py`](file:///Users/jay/projects/quantum-sudoku/backend/app/quantum/oracle.py) | Constraint oracle construction with phase kickback and uncomputation. |
| [`backend/app/quantum/diffusion.py`](file:///Users/jay/projects/quantum-sudoku/backend/app/quantum/diffusion.py) | Grover diffusion operator ($2|s\rangle\langle s| - I$) circuit synthesis. |
| [`backend/app/quantum/grover.py`](file:///Users/jay/projects/quantum-sudoku/backend/app/quantum/grover.py) | `WindowRunner`, BBHT adaptive iteration search, and Aer simulator runner. |
| [`backend/app/quantum/hybrid_solver.py`](file:///Users/jay/projects/quantum-sudoku/backend/app/quantum/hybrid_solver.py) | Main hybrid quantum-classical solving engine with stack-based backtracking. |
| [`backend/app/classical/backtracking.py`](file:///Users/jay/projects/quantum-sudoku/backend/app/classical/backtracking.py) | Bitmask classical backtracking solver used for benchmarking. |
| [`frontend/src/App.jsx`](file:///Users/jay/projects/quantum-sudoku/frontend/src/App.jsx) | Root React application container coordinating grid, controls, and visualizers. |
| [`frontend/src/components/SudokuGrid.jsx`](file:///Users/jay/projects/quantum-sudoku/frontend/src/components/SudokuGrid.jsx) | Interactive 4×4 & 9×9 Sudoku grid with box borders and keypad controls. |
| [`frontend/src/components/StepExplainer.jsx`](file:///Users/jay/projects/quantum-sudoku/frontend/src/components/StepExplainer.jsx) | Step-by-step algorithm walkthrough with mathematical formulas. |
| [`frontend/src/components/ProbabilityChart.jsx`](file:///Users/jay/projects/quantum-sudoku/frontend/src/components/ProbabilityChart.jsx) | Visual probability distribution chart comparing pre- and post-Grover states. |
