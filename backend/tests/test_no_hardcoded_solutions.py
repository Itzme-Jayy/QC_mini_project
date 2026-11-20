"""Fails if any solver/quantum source file contains something shaped like a stored grid."""
import pathlib
import re

APP = pathlib.Path(__file__).resolve().parents[1] / "app"
DIGITS_81 = re.compile(r"\d{81}")
LIST_81 = re.compile(r"(?:\d\s*,\s*){80}\d")


def test_no_81_digit_literals_or_81_item_lists():
    offenders = []
    for folder in ("quantum", "classical", "services", "core", "routes"):
        for f in (APP / folder).rglob("*.py"):
            text = f.read_text()
            if DIGITS_81.search(text) or LIST_81.search(text):
                offenders.append(str(f))
    assert offenders == []
