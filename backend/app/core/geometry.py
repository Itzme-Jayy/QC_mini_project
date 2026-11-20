"""Sudoku board geometry for 9x9 and 4x4 boards."""


class BoardGeometry:
    def __init__(self, size=9):
        self.size = size
        self.num_cells = size * size
        self.box_dim = int(size ** 0.5)
        self.rows = [[r * size + c for c in range(size)] for r in range(size)]
        self.cols = [[r * size + c for r in range(size)] for c in range(size)]
        self.boxes = [
            [(br * self.box_dim + r) * size + bc * self.box_dim + c
             for r in range(self.box_dim) for c in range(self.box_dim)]
            for br in range(self.box_dim) for bc in range(self.box_dim)
        ]
        self.units = self.rows + self.cols + self.boxes
        self.peers = []
        for p in range(self.num_cells):
            r = p // size
            c = p % size
            b = (r // self.box_dim) * self.box_dim + (c // self.box_dim)
            s = set(self.rows[r]) | set(self.cols[c]) | set(self.boxes[b])
            s.discard(p)
            self.peers.append(sorted(s))
        self.peer_sets = [frozenset(x) for x in self.peers]

    def shares_unit(self, a, b):
        return b in self.peer_sets[a]


GEOMETRY_9 = BoardGeometry(9)
GEOMETRY_4 = BoardGeometry(4)


def get_geometry(num_cells_or_size=81):
    if num_cells_or_size in (4, 16):
        return GEOMETRY_4
    return GEOMETRY_9


ROWS = GEOMETRY_9.rows
COLS = GEOMETRY_9.cols
BOXES = GEOMETRY_9.boxes
UNITS = GEOMETRY_9.units
PEERS = GEOMETRY_9.peers
PEER_SETS = GEOMETRY_9.peer_sets


def row_of(p, size=9):
    return p // size


def col_of(p, size=9):
    return p % size


def box_of(p, size=9):
    box_dim = int(size ** 0.5)
    return (p // (size * box_dim)) * box_dim + (p % size) // box_dim


def shares_unit(a, b, geom=None):
    if geom is not None:
        return geom.shares_unit(a, b)
    return b in PEER_SETS[a]
