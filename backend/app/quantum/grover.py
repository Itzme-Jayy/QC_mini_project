"""Grover search on one window, run on the local Aer statevector simulator.

The number of valid assignments M in a window is unknown, so we use the BBHT strategy
(Boyer, Brassard, Hoyer, Tapp): pick a random iteration count j below a bound m, run,
sample, verify classically; if nothing valid shows up, grow m by 6/5 (up to sqrt(N)).
Small variation: j is drawn from 1..m (not 0..m-1) so amplification is always exercised.
"""
import math

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import qiskit_aer.library  # noqa: F401  (adds QuantumCircuit.save_probabilities)

from .circuit_export import export_circuit
from .diffusion import build_diffusion
from .encoding import decode_state, indices_to_digits
from .oracle import build_oracle, is_valid_assignment

_SIM = None
FULL_ENUM_LIMIT = 4096  # classify every basis state for the chart/diagnostics up to this size


def _sim():
    global _SIM
    if _SIM is None:
        _SIM = AerSimulator(method="statevector")
    return _SIM


def _grover_circuit(n_total, n_data, superposition, iteration, j):
    qc = QuantumCircuit(n_total, n_data)
    qc.compose(superposition, inplace=True)
    for _ in range(j):
        qc.compose(iteration, inplace=True)
    qc.save_probabilities(list(range(n_data)))
    qc.measure(list(range(n_data)), list(range(n_data)))
    return qc


def simulate(qc, shots, seed):
    tqc = transpile(qc, _sim(), optimization_level=0)
    res = _sim().run(tqc, shots=shots, seed_simulator=seed).result()
    counts = {int(k, 2): v for k, v in res.get_counts().items()}
    probs = np.asarray(res.data(0)["probabilities"], dtype=float)
    return counts, probs


class WindowRunner:
    """Builds the oracle/diffusion once per (window, exclusions) and runs Grover attempts."""

    def __init__(self, cells, n_data, excluded=()):
        self.cells, self.n_data = cells, n_data
        self.oracle, self.flags = build_oracle(cells, n_data, excluded)
        self.n_total = self.oracle.num_qubits
        self.diffusion = build_diffusion(self.n_total, n_data)
        self.iteration = self.oracle.compose(self.diffusion)
        self.superposition = QuantumCircuit(self.n_total)
        self.superposition.h(range(n_data))
        self.N = 1 << n_data
        self._valid = {}

    def valid(self, state):
        if state not in self._valid:
            self._valid[state] = is_valid_assignment(self.cells, decode_state(self.cells, state))
        return self._valid[state]

    def probabilities_after(self, j, seed=0):
        """Exact outcome distribution after j Grover iterations (also returns sampled counts)."""
        return simulate(_grover_circuit(self.n_total, self.n_data, self.superposition, self.iteration, j), 1, seed)[1]

    def stats(self, probs):
        """Success probability and valid-state count (full enumeration only for small windows)."""
        if self.N <= FULL_ENUM_LIMIT:
            valid = [s for s in range(self.N) if self.valid(s)]
            return float(sum(probs[s] for s in valid)), len(valid)
        top = np.argsort(probs)[::-1][:256]
        return float(sum(probs[s] for s in top if self.valid(int(s)))), None

    def outcomes(self, probs, limit=24):
        order = [int(s) for s in np.argsort(probs)[::-1][:limit]]
        out = []
        for s in order:
            idx = decode_state(self.cells, s)
            out.append({"state": s, "bits": format(s, f"0{self.n_data}b"), "p": float(probs[s]),
                        "valid": self.valid(s), "digits": indices_to_digits(self.cells, idx)})
        return out

    def run(self, *, shots, rng, max_attempts):
        """BBHT loop. Returns a dict describing everything that happened."""
        m, lam, root = 1.0, 6 / 5, math.sqrt(self.N)
        attempts, found, total_iters = [], {}, 0
        win_j, win_probs = 0, None
        for a in range(max_attempts):
            j = 1 + int(rng.integers(0, max(1, int(m))))  # BBHT variant: always at least one iteration
            seed = int(rng.integers(0, 2**31 - 1))
            counts, probs = simulate(
                _grover_circuit(self.n_total, self.n_data, self.superposition, self.iteration, j), shots, seed)
            total_iters += j
            hits = {s: c for s, c in counts.items() if self.valid(s)}
            attempts.append({"attempt": a + 1, "iterations": j, "bound": round(m, 2), "shots": shots,
                             "valid_samples": sum(hits.values()), "found": bool(hits)})
            if hits:
                for s, c in hits.items():
                    found[s] = found.get(s, 0) + c
                win_j, win_probs = j, probs
                break
            win_j, win_probs = j, probs
            m = min(lam * m, root)
        shown_j, shown_probs, note = win_j, win_probs, None
        if found and win_j == 0:  # lucky uniform hit: also show what one iteration does
            shown_j = 1
            shown_probs = self.probabilities_after(1)
            note = "The first uniform sample already hit a valid state; the chart shows one extra illustrative iteration."
        success, m_valid = self.stats(shown_probs)
        uniform = np.full(self.N, 1.0 / self.N)
        ordered = [s for s, _ in sorted(found.items(), key=lambda kv: -kv[1])]
        theta = math.asin(math.sqrt(m_valid / self.N)) if m_valid else None
        return {
            "found_states": ordered, "attempts": attempts, "total_iterations": total_iters,
            "shown_iterations": shown_j, "success_probability": success, "valid_count": m_valid,
            "theta": theta,
            "optimal_iterations": round(math.pi / (4 * theta) - 0.5) if theta else None,
            "before": self.outcomes(uniform, 24) if self.N <= 64 else self._before_subset(shown_probs),
            "after": self.outcomes(shown_probs, 24), "note": note,
        }

    def _before_subset(self, probs):
        """Uniform probability for the same outcomes that are shown after amplification."""
        out = []
        for o in self.outcomes(probs, 24):
            out.append({**o, "p": 1.0 / self.N})
        return out

    def describe(self, iterations):
        return export_circuit(self.cells, self.n_data, self.flags, self.superposition,
                              {"oracle": self.oracle, "diffusion": self.diffusion}, iterations)

    def metrics(self):
        return {"qubits": self.n_total, "data_qubits": self.n_data, "ancillas": len(self.flags),
                "depth_per_iteration": self.iteration.depth(),
                "gate_counts": {k: int(v) for k, v in self.iteration.count_ops().items()}}
