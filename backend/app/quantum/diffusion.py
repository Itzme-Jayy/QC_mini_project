"""Grover diffusion operator D = H^n (2|0><0| - I) H^n over the data qubits.

It reflects every amplitude about the mean, which turns the oracle's sign flip into a
growth of the marked amplitudes."""
from qiskit import QuantumCircuit

from .oracle import mcz


def build_diffusion(n_total, n_data):
    qc = QuantumCircuit(n_total, name="diffusion")
    data = list(range(n_data))
    qc.h(data)
    qc.x(data)
    mcz(qc, data)
    qc.x(data)
    qc.h(data)
    return qc
