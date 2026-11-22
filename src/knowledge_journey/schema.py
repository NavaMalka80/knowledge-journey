"""Export the game model as JSON Schema: the single source of truth for JS clients."""

import json
from pathlib import Path
from typing import Any

from knowledge_journey.models import Game

SCHEMA_PATH = Path("schema") / "game.schema.json"


def game_schema() -> dict[str, Any]:
    """The JSON Schema of a game file.

    Cross-field rules (anchor question, template counts, references) live in the
    Python validators and are not expressible here; the schema covers structure.
    """
    schema = Game.model_json_schema()
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", **schema}


def render_schema() -> str:
    """The schema as stable, human-readable JSON text (ends with a newline)."""
    return json.dumps(game_schema(), ensure_ascii=False, indent=2) + "\n"
