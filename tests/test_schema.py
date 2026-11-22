"""The committed JSON Schema must match the model, and accept the sample game."""

import json
from typing import Any

import jsonschema

from conftest import ROOT
from knowledge_journey.schema import SCHEMA_PATH, game_schema, render_schema


def test_committed_schema_is_up_to_date() -> None:
    committed = (ROOT / SCHEMA_PATH).read_text(encoding="utf-8")
    assert committed == render_schema(), "Run: uv run kj schema -o schema/game.schema.json"


def test_schema_accepts_the_sample_game(game_data: dict[str, Any]) -> None:
    jsonschema.validate(game_data, game_schema())


def test_schema_rejects_a_question_with_three_answers(game_data: dict[str, Any]) -> None:
    game_data["anchor_question"]["answers"].pop()
    validator = jsonschema.Draft202012Validator(game_schema())
    assert not validator.is_valid(game_data)


def test_schema_is_plain_json() -> None:
    assert json.loads(render_schema())["title"] == "Game"
