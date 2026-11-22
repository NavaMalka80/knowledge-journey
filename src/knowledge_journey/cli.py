"""Command-line interface: ``kj validate game.json`` and ``kj schema``."""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from pydantic import ValidationError

from knowledge_journey import __version__
from knowledge_journey.errors import format_errors
from knowledge_journey.models import Game
from knowledge_journey.schema import render_schema

EXIT_OK = 0
EXIT_INVALID = 1
EXIT_UNREADABLE = 2


def _validate(path: Path) -> int:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        print(f"✗ לא הצלחתי לקרוא את הקובץ: {path}", file=sys.stderr)
        return EXIT_UNREADABLE
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"✗ הקובץ אינו JSON תקין (שורה {exc.lineno}, עמודה {exc.colno})", file=sys.stderr)
        return EXIT_UNREADABLE

    try:
        game = Game.model_validate(data)
    except ValidationError as exc:
        errors = format_errors(exc)
        print(f"✗ {path}: נמצאו {len(errors)} בעיות", file=sys.stderr)
        for line in errors:
            print(f"  • {line}", file=sys.stderr)
        return EXIT_INVALID

    print(f"✓ {path}: המשחק '{game.title}' תקין ({len(game.questions())} שאלות)")
    return EXIT_OK


def _schema(output: Path | None) -> int:
    text = render_schema()
    if output is None:
        sys.stdout.write(text)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"✓ ה-Schema נכתב אל {output}")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kj", description="מסע הידע: כלי שורת פקודה")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="בדיקת קובץ משחק")
    validate.add_argument("path", type=Path, help="נתיב לקובץ JSON של משחק")

    schema = commands.add_parser("schema", help="ייצוא JSON Schema של קובץ משחק")
    schema.add_argument("-o", "--output", type=Path, help="קובץ יעד (ברירת מחדל: הדפסה)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "validate":
        return _validate(args.path)
    return _schema(args.output)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
