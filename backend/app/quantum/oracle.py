"""Constraint-based phase oracle for a window of cells.

Qubit layout:   [ data qubits of window cells ... | flag ancillas ... ]

A *flag* is an ancilla that is set to 1 when one constraint is violated:
  * conflict flag  (cell i, cell j, digit d): i and j share a row/column/box and both hold d
  * invalid flag   (cell i, block):           cell i's index does not name a candidate
  * excluded flag  (assignment):              the data register equals an assignment that was
                                              already tried and led to a dead end

The oracle is built generically from those rules. It stores no solution:
  1. compute every flag with a multi-controlled X,
  2. flip the phase when ALL flags are 0   ->  |x> becomes -|x> exactly when x is valid,
  3. uncompute the flags so every ancilla returns to |0>.
"""
from qiskit import QuantumCircuit

from ..core.geometry import get_geometry, shares_unit
from .encoding import invalid_blocks


def conflict_pairs(cells):
    out = []
    board_size = cells[0].board_size if cells else 9
    geom = get_geometry(board_size)
    for i in range(len(cells)):
        for j in range(i + 1, len(cells)):
            if geom.shares_unit(cells[i].pos, cells[j].pos):
                for d in sorted(set(cells[i].cands) & set(cells[j].cands)):
                    out.append((i, j, d))
    return out


def invalid_flags(cells):
    return [(i, start, s) for i, c in enumerate(cells) for start, s in invalid_blocks(c.k, c.nbits)]


def flag_count(cells):
    return len(conflict_pairs(cells)) + len(invalid_flags(cells))


def is_valid_assignment(cells, indices):
    """Classical truth function the oracle implements (used for verification and tests)."""
    for c, i in zip(cells, indices):
        if i >= c.k:
            return False
    n = len(cells)
    board_size = cells[0].board_size if cells else 9
    geom = get_geometry(board_size)
    for a in range(n):
        for b in range(a + 1, n):
            if geom.shares_unit(cells[a].pos, cells[b].pos) and cells[a].cands[indices[a]] == cells[b].cands[indices[b]]:
                return False
    return True


def mcz(qc, qubits):
    """Multi-controlled Z on `qubits` (H - MCX - H on the last one)."""
    if len(qubits) == 1:
        qc.z(qubits[0])
    else:
        qc.h(qubits[-1])
        qc.mcx(list(qubits[:-1]), qubits[-1])
        qc.h(qubits[-1])


def _flag_gate(qc, controls, target):
    """MCX that fires when each control qubit equals its required bit."""
    zeros = [q for q, bit in controls if bit == 0]
    for q in zeros:
        qc.x(q)
    qc.mcx([q for q, _ in controls], target)
    for q in zeros:
        qc.x(q)


def _equals(cell, idx):
    return [(q, (idx >> b) & 1) for b, q in enumerate(cell.qubits)]


def build_oracle(cells, n_data, excluded=()):
    """Return (circuit, flags). `flags` describes each ancilla for the circuit view."""
    specs = []
    board_size = cells[0].board_size if cells else 9
    for i, j, d in conflict_pairs(cells):
        ctrl = _equals(cells[i], cells[i].cands.index(d)) + _equals(cells[j], cells[j].cands.index(d))
        ri, ci = cells[i].pos // board_size + 1, cells[i].pos % board_size + 1
        rj, cj = cells[j].pos // board_size + 1, cells[j].pos % board_size + 1
        specs.append(({"kind": "conflict", "label": f"conflict r{ri}c{ci}~r{rj}c{cj}={d}"}, ctrl))
    for i, start, s in invalid_flags(cells):
        c = cells[i]
        ctrl = [(q, (start >> b) & 1) for b, q in enumerate(c.qubits) if b >= s]
        rc, cc = c.pos // board_size + 1, c.pos % board_size + 1
        specs.append(({"kind": "invalid", "label": f"invalid r{rc}c{cc}"}, ctrl))
    for assignment in excluded:
        ctrl = [bit for c, idx in zip(cells, assignment) for bit in _equals(c, idx)]
        specs.append(({"kind": "excluded", "label": "tried"}, ctrl))

    qc = QuantumCircuit(n_data + len(specs), name="oracle")
    flags = []
    for k, (info, _) in enumerate(specs):
        flags.append({**info, "qubit": n_data + k})
    if not specs:
        return qc, flags  # no constraints: every state is valid, nothing to mark
    compute = QuantumCircuit(qc.num_qubits)
    for k, (_, ctrl) in enumerate(specs):
        _flag_gate(compute, ctrl, n_data + k)
    flag_qubits = [n_data + k for k in range(len(specs))]
    qc.compose(compute, inplace=True)
    for q in flag_qubits:
        qc.x(q)
    mcz(qc, flag_qubits)          # phase flip when every flag is 0
    for q in flag_qubits:
        qc.x(q)
    qc.compose(compute.inverse(), inplace=True)  # uncompute ancillas
    return qc, flags
