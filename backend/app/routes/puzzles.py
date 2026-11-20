from flask import Blueprint, jsonify, request

from ..services import generator, validator

bp = Blueprint("puzzles", __name__)


@bp.post("/puzzles/validate")
def validate():
    body = request.get_json(silent=True) or {}
    try:
        grid = validator.parse_grid(body.get("grid"))
    except ValueError as e:
        return jsonify({"valid": False, "error": str(e)}), 400
    conflicts = validator.find_conflicts(grid)
    return jsonify({"valid": not conflicts, "conflicts": conflicts, "givens": sum(1 for v in grid if v)})


@bp.post("/puzzles/generate")
def generate():
    body = request.get_json(silent=True) or {}
    try:
        size = int(body.get("size", 9))
        if size not in (4, 9):
            size = 9
    except (TypeError, ValueError):
        size = 9

    clues_val = body.get("clues")
    try:
        clues = int(clues_val) if clues_val is not None else None
    except (TypeError, ValueError):
        return jsonify({"error": "clues must be an integer."}), 400

    puzzle = generator.generate_puzzle(clues=clues, seed=body.get("seed"), size=size)
    return jsonify(puzzle)
