"""Truth-table test: the oracle flips the phase exactly on assignments that satisfy every constraint."""
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from app.quantum.encoding import bits_for, decode_state, WindowCell, assign_qubits, invalid_blocks
from app.quantum.oracle import build_oracle, is_valid_assignment
from app.quantum.propagation import candidates
from app.quantum.window import choose_window
from app.services.generator import generate_puzzle


def _check(cells, n_data, excluded=()):
    oracle, flags = build_oracle(cells, n_data, excluded)
    qc = QuantumCircuit(oracle.num_qubits)
    qc.h(range(n_data))
    qc.compose(oracle, inplace=True)
    sv = Statevector.from_label("0" * oracle.num_qubits).evolve(qc)
    amp = np.asarray(sv.data)
    N = 1 << n_data
    assert np.isclose(sum(abs(amp[s]) ** 2 for s in range(N)), 1.0)  # ancillas back to |0>
    for s in range(N):
        idx = decode_state(cells, s)
        want_valid = is_valid_assignment(cells, idx) and idx not in excluded
        sign = np.sign(amp[s].real)
        assert np.isclose(abs(amp[s]), 1 / np.sqrt(N))
        assert (sign < 0) == want_valid, (s, idx)


def test_oracle_matches_brute_force_on_real_windows():
    for seed in (1, 2):
        puzzle = generate_puzzle(30, seed=seed)["grid"]
        cands = candidates(puzzle)
        cells, n_data = choose_window(cands, 14)
        assert n_data + len(build_oracle(cells, n_data)[1]) <= 14
        _check(cells, n_data)


def test_oracle_rejects_excluded_assignments():
    puzzle = generate_puzzle(30, seed=3)["grid"]
    cells, n_data = choose_window(candidates(puzzle), 12)
    good = [decode_state(cells, s) for s in range(1 << n_data)
            if is_valid_assignment(cells, decode_state(cells, s))]
    assert good
    _check(cells, n_data, excluded=(good[0],))


def test_invalid_blocks_cover_exactly_the_unused_indices():
    for k in range(2, 10):
        m = bits_for(k)
        covered = sorted(i for start, s in invalid_blocks(k, m) for i in range(start, start + (1 << s)))
        assert covered == list(range(k, 1 << m))
