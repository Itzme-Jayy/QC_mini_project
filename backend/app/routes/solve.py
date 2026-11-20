from flask import Blueprint, current_app, jsonify, request

from ..extensions import db
from ..models import SolveRun
from ..services import comparison_service, solver_service, validator

bp = Blueprint("solve", __name__)


def _checked_grid(body):
    """Parse and validate input. Returns (grid, error_response)."""
    try:
        grid = validator.parse_grid(body.get("grid"))
    except ValueError as e:
        return None, (jsonify({"error": str(e)}), 400)
    conflicts = validator.find_conflicts(grid)
    if conflicts:
        return None, (jsonify({"error": "The givens break Sudoku rules.", "conflicts": conflicts}), 400)
    if not solver_service.is_solvable(grid):
        return None, (jsonify({"error": "This puzzle has no solution."}), 422)
    return grid, None


def _opts(body):
    try:
        use_singles = body.get("use_singles")
        if use_singles is None:
            use_singles = body.get("propagation", True)
        return {"qubit_budget": body.get("qubit_budget"), "shots": body.get("shots"),
                "use_singles": bool(use_singles), "seed": body.get("seed")}
    except (TypeError, ValueError):
        return {}


@bp.post("/solve/quantum")
def quantum():
    body = request.get_json(silent=True) or {}
    grid, err = _checked_grid(body)
    if err:
        return err
    return jsonify(solver_service.solve_quantum(grid, current_app.config, **_opts(body)))


@bp.post("/solve/classical")
def classical():
    body = request.get_json(silent=True) or {}
    grid, err = _checked_grid(body)
    if err:
        return err
    return jsonify(solver_service.solve_classical(grid))


@bp.post("/solve/compare")
def compare():
    body = request.get_json(silent=True) or {}
    grid, err = _checked_grid(body)
    if err:
        return err
    return jsonify(comparison_service.compare(grid, current_app.config, **_opts(body)))


@bp.get("/runs")
def runs():
    rows = SolveRun.query.order_by(SolveRun.id.desc()).limit(50).all()
    return jsonify([r.to_dict() for r in rows])


@bp.get("/runs/<int:run_id>")
def run_detail(run_id):
    run = db.session.get(SolveRun, run_id)
    if run is None:
        return jsonify({"error": "Run not found."}), 404
    return jsonify({**run.to_dict(), "trace": [s.to_dict() for s in run.steps]})
