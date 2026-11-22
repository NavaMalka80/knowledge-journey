"""Turn Pydantic validation errors into short Hebrew messages for teachers."""

from pydantic import ValidationError
from pydantic_core import ErrorDetails

# Hebrew wording for the built-in Pydantic error types we expect to meet.
# Anything missing here falls back to Pydantic's English message.
_MESSAGES: dict[str, str] = {
    "missing": "שדה חובה חסר",
    "extra_forbidden": "שדה לא מוכר (אולי שגיאת כתיב בשם השדה?)",
    "string_type": "צריך להיות טקסט",
    "string_too_short": "לא יכול להיות ריק",
    "string_pattern_mismatch": "מזהה יכול לכלול רק אותיות לועזיות קטנות, ספרות ומקף",
    "int_type": "צריך להיות מספר שלם",
    "int_parsing": "צריך להיות מספר שלם",
    "bool_type": "צריך להיות true או false",
    "list_type": "צריך להיות רשימה",
    "enum": "ערך לא מוכר. הערכים האפשריים: {expected}",
    "literal_error": "ערך לא מוכר. הערכים האפשריים: {expected}",
    "union_tag_invalid": "סוג שלב לא מוכר. הסוגים האפשריים: {expected_tags}",
    "union_tag_not_found": "לשלב חסר השדה type",
    "greater_than_equal": "צריך להיות לפחות {ge}",
    "less_than_equal": "צריך להיות לכל היותר {le}",
}


def _too_short(ctx: dict[str, object]) -> str:
    return f"צריכים להיות לפחות {ctx['min_length']} פריטים, ויש {ctx['actual_length']}"


def _too_long(ctx: dict[str, object]) -> str:
    return f"צריכים להיות לכל היותר {ctx['max_length']} פריטים, ויש {ctx['actual_length']}"


def format_location(loc: tuple[int | str, ...]) -> str:
    """``("stations", 2, "steps", 0)`` -> ``stations[2].steps[0]``."""
    out = ""
    for part in loc:
        if isinstance(part, int):
            out += f"[{part}]"
        else:
            out += f".{part}" if out else part
    return out


def _drop_union_tags(loc: tuple[int | str, ...]) -> tuple[int | str, ...]:
    """Remove the step-type tag Pydantic inserts after ``steps[i]``.

    ``stations[3].steps[1].question.question.text`` -> ``...steps[1].question.text``.
    """
    out: list[int | str] = []
    for i, part in enumerate(loc):
        if i >= 2 and loc[i - 2] == "steps" and isinstance(loc[i - 1], int):
            continue
        out.append(part)
    return tuple(out)


def message(error: ErrorDetails) -> str:
    """The Hebrew message for one error, without its location."""
    kind = error["type"]
    ctx: dict[str, object] = dict(error.get("ctx", {}))
    if kind == "value_error":
        # Raised by our own validators, already in Hebrew.
        return str(ctx.get("error", error["msg"]))
    if kind == "too_short" and "min_length" in ctx:
        return _too_short(ctx)
    if kind == "too_long" and "max_length" in ctx:
        return _too_long(ctx)
    template = _MESSAGES.get(kind)
    if template is None:
        return error["msg"]
    try:
        return template.format(**ctx)
    except KeyError:
        return template


def format_errors(exc: ValidationError) -> list[str]:
    """One readable line per error: ``where: what``."""
    lines = []
    for error in exc.errors():
        where = format_location(_drop_union_tags(error["loc"]))
        text = message(error)
        lines.append(f"{where}: {text}" if where else text)
    return lines
