from datetime import datetime, timezone

from .extensions import db


def _now():
    return datetime.now(timezone.utc)


class Puzzle(db.Model):
    __tablename__ = "puzzles"
    id = db.Column(db.Integer, primary_key=True)
    grid = db.Column(db.String(81), nullable=False, index=True)  # givens, '0' = empty
    difficulty = db.Column(db.String(16))
    created_at = db.Column(db.DateTime(timezone=True), default=_now)
    runs = db.relationship("SolveRun", backref="puzzle", lazy=True)


class SolveRun(db.Model):
    __tablename__ = "solve_runs"
    id = db.Column(db.Integer, primary_key=True)
    puzzle_id = db.Column(db.Integer, db.ForeignKey("puzzles.id"), nullable=False)
    method = db.Column(db.String(16), nullable=False)  # quantum | classical
    status = db.Column(db.String(16), nullable=False)  # solved | unsolved | timeout
    solved_grid = db.Column(db.String(81))
    duration_ms = db.Column(db.Float)
    qubits_used = db.Column(db.Integer)
    grover_iterations = db.Column(db.Integer)
    backtracks = db.Column(db.Integer)
    nodes_explored = db.Column(db.Integer)
    created_at = db.Column(db.DateTime(timezone=True), default=_now)
    steps = db.relationship(
        "SolveStep", backref="run", lazy=True, order_by="SolveStep.step_index",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id, "puzzle_id": self.puzzle_id, "puzzle": self.puzzle.grid,
            "method": self.method, "status": self.status, "solved_grid": self.solved_grid,
            "duration_ms": self.duration_ms, "qubits_used": self.qubits_used,
            "grover_iterations": self.grover_iterations, "backtracks": self.backtracks,
            "nodes_explored": self.nodes_explored,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SolveStep(db.Model):
    __tablename__ = "solve_steps"
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey("solve_runs.id"), nullable=False, index=True)
    step_index = db.Column(db.Integer, nullable=False)
    step_type = db.Column(db.String(32), nullable=False)
    description = db.Column(db.Text, nullable=False)
    payload = db.Column(db.JSON)

    def to_dict(self):
        return {
            "index": self.step_index, "type": self.step_type,
            "description": self.description, "payload": self.payload or {},
        }
