"""Content rules from REQUIREMENTS section 5, one test per rule."""

from typing import Any

import pytest
from pydantic import ValidationError

from conftest import first_question, station
from knowledge_journey.errors import format_errors
from knowledge_journey.models import Game


def errors_of(data: dict[str, Any]) -> str:
    """Validate and return all Hebrew error lines as one string."""
    with pytest.raises(ValidationError) as caught:
        Game.model_validate(data)
    return "\n".join(format_errors(caught.value))


# ---------------------------------------------------------------- the sample


def test_sample_game_is_valid(game_data: dict[str, Any]) -> None:
    game = Game.model_validate(game_data)
    assert len(game.stations) == 7
    assert len(game.questions()) == 17
    assert len(game.knowledge_items()) == 3


def test_round_trip_keeps_the_game_identical(game_data: dict[str, Any]) -> None:
    game = Game.model_validate(game_data)
    again = Game.model_validate_json(game.model_dump_json())
    assert again == game


# ---------------------------------------------------------------- questions


def test_question_needs_exactly_four_answers(game_data: dict[str, Any]) -> None:
    first_question(game_data, "retrieve")["answers"].pop()
    assert "לפחות 4 פריטים, ויש 3" in errors_of(game_data)


def test_question_cannot_have_five_answers(game_data: dict[str, Any]) -> None:
    first_question(game_data, "retrieve")["answers"].append("תשובה חמישית")
    assert "לכל היותר 4 פריטים" in errors_of(game_data)


def test_correct_answer_must_be_one_of_the_four(game_data: dict[str, Any]) -> None:
    first_question(game_data, "retrieve")["correct_index"] = 4
    assert "correct_index: צריך להיות לכל היותר 3" in errors_of(game_data)


def test_rationale_is_required(game_data: dict[str, Any]) -> None:
    del first_question(game_data, "retrieve")["rationale"]
    assert "rationale: שדה חובה חסר" in errors_of(game_data)


def test_rationale_cannot_be_blank(game_data: dict[str, Any]) -> None:
    first_question(game_data, "retrieve")["rationale"] = "   "
    assert "rationale: לא יכול להיות ריק" in errors_of(game_data)


def test_answers_must_differ(game_data: dict[str, Any]) -> None:
    question = first_question(game_data, "retrieve")
    question["answers"][3] = question["answers"][0]
    assert "תשובות כפולות" in errors_of(game_data)


# ---------------------------------------------------------------- goals and ideas


@pytest.mark.parametrize("count", [3, 7])
def test_four_to_six_learning_goals(game_data: dict[str, Any], count: int) -> None:
    goals = game_data["identity"]["learning_goals"]
    while len(goals) < count:
        goals.append({"id": f"goal-extra-{len(goals)}", "text": "מטרה נוספת"})
    del goals[count:]
    assert "learning_goals" in errors_of(game_data)


@pytest.mark.parametrize("count", [2, 6])
def test_three_to_five_key_ideas(game_data: dict[str, Any], count: int) -> None:
    ideas = game_data["key_ideas"]
    while len(ideas) < count:
        ideas.append(f"רעיון {len(ideas)}")
    del ideas[count:]
    assert "key_ideas" in errors_of(game_data)


def test_age_range_must_be_ordered(game_data: dict[str, Any]) -> None:
    game_data["identity"]["age_min"] = 13
    assert "גיל מינימלי גדול מגיל מקסימלי" in errors_of(game_data)


def test_mode_must_be_learning_or_review(game_data: dict[str, Any]) -> None:
    game_data["identity"]["mode"] = "exam"
    assert "'learning'" in errors_of(game_data)


# ---------------------------------------------------------------- anchor and transfer


def test_anchor_must_appear_in_station_seven(game_data: dict[str, Any]) -> None:
    seal = station(game_data, "seal")
    seal["steps"] = [s for s in seal["steps"] if s["type"] != "anchor"]
    seal["steps"].append({"type": "question", "question": dict(game_data["anchor_question"])})
    assert "תחנת חותם הידע: צריכה להופיע בה שאלת העוגן" in errors_of(game_data)


def test_anchor_cannot_appear_in_middle_stations(game_data: dict[str, Any]) -> None:
    station(game_data, "crack")["steps"].append({"type": "anchor"})
    assert "שאלת העוגן מופיעה רק בתחנה 1 ובתחנה 7" in errors_of(game_data)


def test_transfer_question_must_be_new(game_data: dict[str, Any]) -> None:
    transfer = first_question(game_data, "seal")
    transfer["text"] = game_data["anchor_question"]["text"] + "  "
    assert "שאלת ההעברה בתחנה 7 צריכה להיות חדשה" in errors_of(game_data)


# ---------------------------------------------------------------- template


def test_stations_must_keep_fixed_order(game_data: dict[str, Any]) -> None:
    stations = game_data["stations"]
    stations[1], stations[2] = stations[2], stations[1]
    assert "התחנות צריכות להופיע בסדר הקבוע" in errors_of(game_data)


def test_exactly_seven_stations(game_data: dict[str, Any]) -> None:
    game_data["stations"].pop()
    assert "stations: צריכים להיות לפחות 7 פריטים" in errors_of(game_data)


def test_station_duration_follows_template(game_data: dict[str, Any]) -> None:
    station(game_data, "crack")["duration_minutes"] = 10
    assert "תחנת מפצחים: המשך צריך להיות 8 דקות" in errors_of(game_data)


def test_retrieve_station_needs_six_tasks(game_data: dict[str, Any]) -> None:
    station(game_data, "retrieve")["steps"].pop()
    assert "תחנת שולפים: מספר השאלות צריך להיות 6, ויש 5" in errors_of(game_data)


def test_discover_station_needs_three_knowledge_keys(game_data: dict[str, Any]) -> None:
    station(game_data, "discover")["steps"].pop()
    assert "תחנת מגלים: מספר פריטי הידע צריך להיות 3, ויש 2" in errors_of(game_data)


def test_championship_needs_at_least_three_questions(game_data: dict[str, Any]) -> None:
    station(game_data, "championship")["steps"].pop()
    assert "לפחות 3 שאלות" in errors_of(game_data)


def test_connect_station_needs_its_case_video(game_data: dict[str, Any]) -> None:
    steps = station(game_data, "connect")["steps"]
    steps[:] = [s for s in steps if s["type"] != "media"]
    assert "תחנת מחברים: מספר פריטי המדיה צריך להיות 1, ויש 0" in errors_of(game_data)


# ---------------------------------------------------------------- references and ids


def test_question_ids_are_unique(game_data: dict[str, Any]) -> None:
    first_question(game_data, "crack")["id"] = "q-r1"
    assert "מזהה שאלה 'q-r1' מופיע יותר מפעם אחת" in errors_of(game_data)


def test_ids_use_a_safe_format(game_data: dict[str, Any]) -> None:
    first_question(game_data, "crack")["id"] = "שאלה 1"
    assert "מזהה יכול לכלול רק" in errors_of(game_data)


def test_knowledge_item_must_point_to_a_real_goal(game_data: dict[str, Any]) -> None:
    station(game_data, "discover")["steps"][0]["item"]["goal_id"] = "goal-missing"
    assert "מפנה למטרה שלא קיימת: 'goal-missing'" in errors_of(game_data)


def test_media_step_must_point_to_real_media(game_data: dict[str, Any]) -> None:
    station(game_data, "spark")["steps"][0]["media_id"] = "m-missing"
    assert "הפניה למדיה שלא קיימת: 'm-missing'" in errors_of(game_data)


@pytest.mark.parametrize(
    "src", ["https://example.com/video.mp4", "/home/teacher/video.mp4", "../outside.mp4"]
)
def test_media_must_be_a_relative_file_in_the_package(game_data: dict[str, Any], src: str) -> None:
    game_data["media"][0]["src"] = src
    assert "נתיב יחסי בתוך החבילה" in errors_of(game_data)


def test_unknown_fields_are_rejected(game_data: dict[str, Any]) -> None:
    first_question(game_data, "retrieve")["rationel"] = "שגיאת כתיב"
    assert "rationel: שדה לא מוכר" in errors_of(game_data)


def test_unknown_step_type_is_rejected(game_data: dict[str, Any]) -> None:
    station(game_data, "crack")["steps"][0]["type"] = "poll"
    assert "סוג שלב לא מוכר" in errors_of(game_data)


# ---------------------------------------------------------------- error formatting


def test_step_type_tag_is_hidden_from_error_paths(game_data: dict[str, Any]) -> None:
    del first_question(game_data, "crack")["text"]
    assert "stations[4].steps[0].question.text: שדה חובה חסר" in errors_of(game_data)


def test_unknown_error_types_fall_back_to_english(game_data: dict[str, Any]) -> None:
    game_data["identity"]["grades"] = "ה'"
    assert "identity.grades: צריך להיות רשימה" in errors_of(game_data)
    game_data["identity"]["grades"] = ["ה'"]
    game_data["identity"]["participants"] = 2.5
    assert "participants:" in errors_of(game_data)
