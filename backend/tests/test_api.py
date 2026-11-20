import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db


@pytest.fixture()
def client():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


def _puzzle(client, clues=34, seed=1):
    return client.post("/api/puzzles/generate", json={"clues": clues, "seed": seed}).get_json()["grid"]


def test_health(client):
    assert client.get("/api/health").get_json()["status"] == "ok"


def test_validate_endpoint(client):
    g = [0] * 81
    g[0] = g[1] = 4
    r = client.post("/api/puzzles/validate", json={"grid": g}).get_json()
    assert r["valid"] is False and r["conflicts"] == [0, 1]
    assert client.post("/api/puzzles/validate", json={"grid": [1, 2]}).status_code == 400


def test_classical_and_history(client):
    g = _puzzle(client)
    r = client.post("/api/solve/classical", json={"grid": g}).get_json()
    assert r["status"] == "solved"
    runs = client.get("/api/runs").get_json()
    assert runs[0]["method"] == "classical"
    assert client.get(f"/api/runs/{r['run_id']}").status_code == 200
    assert client.get("/api/runs/9999").status_code == 404


def test_quantum_and_compare(client):
    g = _puzzle(client, clues=30, seed=3)
    q = client.post("/api/solve/quantum", json={"grid": g, "qubit_budget": 14}).get_json()
    assert q["status"] == "solved" and q["trace"]
    detail = client.get(f"/api/runs/{q['run_id']}").get_json()
    assert len(detail["trace"]) == len(q["trace"])
    c = client.post("/api/solve/compare", json={"grid": g, "qubit_budget": 14}).get_json()
    assert c["classical"]["status"] == "solved" and c["quantum"]["status"] == "solved"
    assert "note" in c["summary"]


def test_rejects_bad_and_unsolvable_puzzles(client):
    assert client.post("/api/solve/quantum", json={"grid": "abc"}).status_code == 400
    g = [0] * 81
    g[0] = g[1] = 4
    assert client.post("/api/solve/quantum", json={"grid": g}).status_code == 400
    g = [0] * 81
    for c in range(1, 9):
        g[c] = c
    g[27] = 9
    r = client.post("/api/solve/quantum", json={"grid": g})
    assert r.status_code == 422 and "no solution" in r.get_json()["error"]


def test_4x4_generation_and_solve(client):
    res = client.post("/api/puzzles/generate", json={"size": 4, "clues": 6, "seed": 4}).get_json()
    assert len(res["grid"]) == 16
    q = client.post("/api/solve/quantum", json={"grid": res["grid"], "qubit_budget": 8}).get_json()
    assert q["status"] == "solved"
    assert len(q["solution"]) == 16
    c = client.post("/api/solve/compare", json={"grid": res["grid"], "qubit_budget": 8}).get_json()
    assert c["classical"]["status"] == "solved" and c["quantum"]["status"] == "solved"

