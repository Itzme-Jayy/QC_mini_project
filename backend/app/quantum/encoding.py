"""Cell encoding.

A cell with k remaining candidates is stored in m = ceil(log2 k) qubits. The basis
state |i> (i = 0 .. 2^m - 1, little-endian) means "the cell holds candidate number i".
Indices i >= k do not name a candidate; the oracle must reject them.
"""
import math
from dataclasses import dataclass, field


def bits_for(k):
    """Qubits needed to index k candidates (0 when the cell is already decided)."""
    return 0 if k <= 1 else math.ceil(math.log2(k))


def invalid_blocks(k, m):
    """Cover the invalid indices [k, 2**m) with aligned blocks [start, start + 2**s).

    Each block is a 'cube' that only fixes the high bits, so one multi-controlled gate
    flags the whole block. At most m blocks are needed per cell.
    """
    blocks, cur, end = [], k, 1 << m
    while cur < end:
        s = 0
        while cur % (1 << (s + 1)) == 0 and cur + (1 << (s + 1)) <= end:
            s += 1
        blocks.append((cur, s))
        cur += 1 << s
    return blocks


@dataclass
class WindowCell:
    pos: int            # board position 0..80 (or 0..15 for 4x4)
    cands: list         # sorted candidate digits
    nbits: int
    board_size: int = 9
    qubits: list = field(default_factory=list)  # qubit indices (little-endian)

    @property
    def k(self):
        return len(self.cands)


def assign_qubits(cells):
    """Give each window cell a contiguous run of data qubits. Returns the data qubit count."""
    nxt = 0
    for c in cells:
        c.qubits = list(range(nxt, nxt + c.nbits))
        nxt += c.nbits
    return nxt


def decode_state(cells, state):
    """Split a measured integer into one candidate index per cell."""
    out = []
    for c in cells:
        idx = 0
        for b, q in enumerate(c.qubits):
            idx |= ((state >> q) & 1) << b
        out.append(idx)
    return tuple(out)


def encode_state(cells, indices):
    state = 0
    for c, idx in zip(cells, indices):
        for b, q in enumerate(c.qubits):
            state |= ((idx >> b) & 1) << q
    return state


def indices_to_digits(cells, indices):
    return [c.cands[i] if i < c.k else None for c, i in zip(cells, indices)]
