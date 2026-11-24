"""The `kj` command-line tool."""

import json
from pathlib import Path
from typing import Any

import pytest

from conftest import SAMPLE_PATH
from knowledge_journey.cli import EXIT_INVALID, EXIT_OK, EXIT_UNREADABLE, main
from knowledge_journey.schema import render_schema


def test_validate_accepts_the_sample(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", str(SAMPLE_PATH)]) == EXIT_OK
    assert "תקין (27 שאלות)" in capsys.readouterr().out


def test_validate_lists_every_problem(
    tmp_path: Path, game_data: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    game_data["anchor_question"]["answers"].append("חמישית")
    del game_data["title"]
    path = tmp_path / "game.json"
    path.write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

    assert main(["validate", str(path)]) == EXIT_INVALID
    err = capsys.readouterr().err
    assert "נמצאו 2 בעיות" in err
    assert "title: שדה חובה חסר" in err
    assert "anchor_question.answers: צריכים להיות לכל היותר 4 פריטים, ויש 5" in err


def test_validate_reports_broken_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "broken.json"
    path.write_text('{"title": ', encoding="utf-8")
    assert main(["validate", str(path)]) == EXIT_UNREADABLE
    assert "אינו JSON תקין" in capsys.readouterr().err


def test_validate_reports_missing_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", str(tmp_path / "nope.json")]) == EXIT_UNREADABLE
    assert "לא הצלחתי לקרוא" in capsys.readouterr().err


def test_schema_prints_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["schema"]) == EXIT_OK
    assert capsys.readouterr().out == render_schema()


def test_schema_writes_to_file(tmp_path: Path) -> None:
    target = tmp_path / "out" / "game.schema.json"
    assert main(["schema", "-o", str(target)]) == EXIT_OK
    assert target.read_text(encoding="utf-8") == render_schema()
