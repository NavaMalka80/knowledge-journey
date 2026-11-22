"""Shared fixtures: a fresh, valid copy of the sample game for every test."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PATH = ROOT / "examples" / "water-cycle.json"
_SAMPLE: dict[str, Any] = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def game_data() -> dict[str, Any]:
    """A valid game as a plain dict. Each test gets its own copy to break."""
    return copy.deepcopy(_SAMPLE)


def station(data: dict[str, Any], kind: str) -> dict[str, Any]:
    """The station of the given kind inside a game dict."""
    found: dict[str, Any] = next(s for s in data["stations"] if s["kind"] == kind)
    return found


def first_question(data: dict[str, Any], kind: str) -> dict[str, Any]:
    """The first regular question of a station."""
    steps = station(data, kind)["steps"]
    found: dict[str, Any] = next(s for s in steps if s["type"] == "question")["question"]
    return found
