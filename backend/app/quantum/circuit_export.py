"""Turn Qiskit circuits into plain JSON gate lists for the frontend SVG renderer."""


def export_gates(circuit):
    gates = []
    for inst in circuit.data:
        qs = [circuit.find_bit(q).index for q in inst.qubits]
        name = inst.operation.name
        if name in ("h", "x", "z"):
            gates.append({"op": name, "qubits": qs})
        elif name in ("cx", "ccx", "mcx") or (name.startswith("c") and name.endswith("x")):
            gates.append({"op": "mcx", "controls": qs[:-1], "target": qs[-1]})
        elif name != "barrier":
            gates.append({"op": name, "qubits": qs})
    return gates


def export_circuit(cells, n_data, flags, superposition, iteration_parts, iterations):
    """Describe one window's circuit: wires, sections and how many times Grover repeats."""
    wires = []
    for c in cells:
        size = getattr(c, "board_size", 9)
        for b, q in enumerate(c.qubits):
            wires.append({"index": q, "kind": "data",
                          "label": f"r{c.pos // size + 1}c{c.pos % size + 1}[{b}]"})
    for f in flags:
        wires.append({"index": f["qubit"], "kind": "ancilla", "label": f["label"]})
    wires.sort(key=lambda w: w["index"])
    return {
        "wires": wires,
        "n_data": n_data,
        "sections": {
            "superposition": export_gates(superposition),
            "oracle": export_gates(iteration_parts["oracle"]),
            "diffusion": export_gates(iteration_parts["diffusion"]),
        },
        "iterations": iterations,
    }
