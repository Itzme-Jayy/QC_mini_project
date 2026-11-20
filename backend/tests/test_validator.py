import pytest

from app.services.generator import generate_puzzle
from app.services.validator import find_conflicts, is_complete_valid, parse_grid, preserves_givens


def test_parse_accepts_list_nested_and_string():
    flat = [0] * 81
    assert parse_grid(flat) == flat
    assert parse_grid([[0] * 9 for _ in range(9)]) == flat
    assert parse_grid("." * 81) == flat


@pytest.mark.parametrize("bad", [[0] * 80, [10] + [0] * 80, ["a"] + [0] * 80, "12", None, [True] + [0] * 80])
def test_parse_rejects_bad_input(bad):
    with pytest.raises(ValueError):
        parse_grid(bad)


def test_conflicts_detect_row_col_box():
    g = [0] * 81
    g[0] = g[8] = 5      # same row
    assert find_conflicts(g) == [0, 8]
    g = [0] * 81
    g[0] = g[72] = 3     # same column
    assert find_conflicts(g) == [0, 72]
    g = [0] * 81
    g[0] = g[10] = 7     # same box
    assert find_conflicts(g) == [0, 10]


def test_generated_puzzle_has_no_conflicts_and_is_not_complete():
    p = generate_puzzle(35, seed=1)
    assert find_conflicts(p["grid"]) == []
    assert not is_complete_valid(p["grid"])


def test_complete_check_and_givens():
    from app.classical.backtracking import solve
    p = generate_puzzle(35, seed=2)["grid"]
    s = solve(p)["solutions"][0]
    assert is_complete_valid(s) and preserves_givens(p, s)
    s[0], s[1] = s[1], s[0]
    assert not is_complete_valid(s)
