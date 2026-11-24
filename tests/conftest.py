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


def stations(data: dict[str, Any]) -> dict[str, Any]:
    """The seven stations of a game dict, by name."""
    found: dict[str, Any] = data["stations"]
    return found
