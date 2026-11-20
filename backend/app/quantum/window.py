"""Pick a small 'quantum window' of empty cells whose circuit fits the qubit budget.

Cost of a window = data qubits + flag ancillas. We start from the most constrained cell
(MRV) and greedily add peer cells that interact with the window, so the oracle has real
constraints to enforce."""
from ..core.geometry import get_geometry
from .encoding import WindowCell, assign_qubits, bits_for
from .oracle import flag_count


def _cells_for(positions, cands, board_size=9):
    cells = [WindowCell(pos=p, cands=list(cands[p]), nbits=bits_for(len(cands[p])), board_size=board_size) for p in positions]
    n_data = assign_qubits(cells)
    return cells, n_data


def window_cost(positions, cands, reserve=0, board_size=9):
    cells, n_data = _cells_for(positions, cands, board_size=board_size)
    return n_data + flag_count(cells) + reserve


def choose_window(cands, budget):
    """Return (cells, n_data) for the next window, or None if nothing is left to decide."""
    num_cells = len(cands)
    geom = get_geometry(num_cells)
    empties = [p for p in range(num_cells) if len(cands[p]) > 1]
    if not empties:
        return None
    empty_set = set(empties)
    seed = min(empties, key=lambda p: (len(cands[p]), -len(geom.peer_sets[p] & empty_set), p))
    chosen = [seed]
    while True:
        best = None
        for p in empties:
            if p in chosen:
                continue
            links = sum(1 for q in chosen if p in geom.peer_sets[q])
            if links == 0:
                continue
            if window_cost(chosen + [p], cands, board_size=geom.size) > budget:
                continue
            score = (-links, len(cands[p]), p)
            if best is None or score < best[0]:
                best = (score, p)
        if best is None:
            break
        chosen.append(best[1])
    cells, n_data = _cells_for(chosen, cands, board_size=geom.size)
    return cells, n_data
