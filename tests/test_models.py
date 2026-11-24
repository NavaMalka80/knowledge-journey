"""Content rules from the requirements and the station specification (ADR 0004)."""

from typing import Any

import pytest
from pydantic import ValidationError

from conftest import stations
from knowledge_journey.errors import format_errors
from knowledge_journey.models import Game
from knowledge_journey.template import CHAMPIONSHIP_ROUNDS


def errors_of(data: dict[str, Any]) -> str:
    """Validate and return all Hebrew error lines as one string."""
    with pytest.raises(ValidationError) as caught:
        Game.model_validate(data)
    return "\n".join(format_errors(caught.value))


# ---------------------------------------------------------------- the sample


def test_sample_game_is_valid(game_data: dict[str, Any]) -> None:
    game = Game.model_validate(game_data)
    assert len(game.questions()) == 27
    assert game.identity.theme == "forest"


def test_round_trip_keeps_the_game_identical(game_data: dict[str, Any]) -> None:
    game = Game.model_validate(game_data)
    assert Game.model_validate_json(game.model_dump_json()) == game


def test_old_schema_version_is_rejected(game_data: dict[str, Any]) -> None:
    game_data["schema_version"] = 1
    assert "schema_version" in errors_of(game_data)


# ---------------------------------------------------------------- questions


def test_question_needs_at_least_two_answers(game_data: dict[str, Any]) -> None:
    game_data["anchor_question"]["answers"] = ["רק אחת"]
    game_data["anchor_question"]["correct_index"] = 0
    assert "לפחות 2 פריטים, ויש 1" in errors_of(game_data)


def test_question_cannot_have_five_answers(game_data: dict[str, Any]) -> None:
    game_data["anchor_question"]["answers"].append("חמישית")
    assert "לכל היותר 4 פריטים" in errors_of(game_data)


def test_two_answers_are_allowed(game_data: dict[str, Any]) -> None:
    game_data["anchor_question"]["answers"] = ["כן", "לא"]
    game_data["anchor_question"]["correct_index"] = 0
    Game.model_validate(game_data)


def test_correct_answer_must_exist(game_data: dict[str, Any]) -> None:
    question = stations(game_data)["retrieve"]["recall"][1]
    question["answers"] = ["שלג", "ערפל"]
    question["correct_index"] = 3
    assert "התשובה הנכונה (מספר 4) לא קיימת: יש רק 2 תשובות" in errors_of(game_data)


def test_rationale_is_required(game_data: dict[str, Any]) -> None:
    del stations(game_data)["retrieve"]["recall"][0]["rationale"]
    assert "rationale: שדה חובה חסר" in errors_of(game_data)


def test_answers_must_differ(game_data: dict[str, Any]) -> None:
    answers = game_data["anchor_question"]["answers"]
    answers[3] = answers[0]
    assert "תשובות כפולות" in errors_of(game_data)


def test_vote_time_must_be_reasonable(game_data: dict[str, Any]) -> None:
    game_data["anchor_question"]["vote_seconds"] = 2
    assert "vote_seconds: צריך להיות לפחות 5" in errors_of(game_data)


# ---------------------------------------------------------------- identity and ideas


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


def test_theme_must_be_one_of_the_four(game_data: dict[str, Any]) -> None:
    game_data["identity"]["theme"] = "space"
    assert "'city'" in errors_of(game_data)


# ---------------------------------------------------------------- station 1


@pytest.mark.parametrize("count", [1, 4])
def test_two_or_three_opening_goals(game_data: dict[str, Any], count: int) -> None:
    stations(game_data)["spark"]["opening_goals"] = [f"מטרה {i}" for i in range(count)]
    assert "opening_goals" in errors_of(game_data)


def test_opening_media_must_be_a_video(game_data: dict[str, Any]) -> None:
    stations(game_data)["spark"]["opening_media_id"] = "m-cloud"
    assert "'m-cloud' צריך להיות סרטון" in errors_of(game_data)


# ---------------------------------------------------------------- station 2


def test_discover_has_three_named_keys(game_data: dict[str, Any]) -> None:
    del stations(game_data)["discover"]["understand"]
    assert "stations.discover.understand: שדה חובה חסר" in errors_of(game_data)


def test_key_question_needs_reinforcement(game_data: dict[str, Any]) -> None:
    stations(game_data)["discover"]["identify"]["question"]["reinforcement"] = ""
    assert "לשאלת מפתח צריך הסבר חיזוק" in errors_of(game_data)


def test_key_needs_a_key_word(game_data: dict[str, Any]) -> None:
    del stations(game_data)["discover"]["identify"]["key_word"]
    assert "key_word: שדה חובה חסר" in errors_of(game_data)


def test_examples_come_in_pairs(game_data: dict[str, Any]) -> None:
    stations(game_data)["discover"]["distinguish"]["examples"].pop()
    assert "צריך שתיים או אף אחת" in errors_of(game_data)


def test_content_needs_text_or_media(game_data: dict[str, Any]) -> None:
    stations(game_data)["discover"]["distinguish"]["knowledge"] = {"title": "ריק"}
    assert "תוכן חייב לכלול טקסט, קובץ מדיה או את שניהם" in errors_of(game_data)


# ---------------------------------------------------------------- station 3


@pytest.mark.parametrize("group", ["recall", "distinguish", "connect"])
def test_retrieve_has_two_tasks_of_each_kind(game_data: dict[str, Any], group: str) -> None:
    stations(game_data)["retrieve"][group].pop()
    assert f"stations.retrieve.{group}: צריכים להיות לפחות 2 פריטים, ויש 1" in errors_of(game_data)


def test_distinguish_task_examples_come_in_pairs(game_data: dict[str, Any]) -> None:
    stations(game_data)["retrieve"]["distinguish"][1]["examples"].pop()
    assert "stations.retrieve.distinguish[1]: דוגמאות להבחנה מוצגות בזוג" in errors_of(game_data)


# ---------------------------------------------------------------- station 4


def test_connect_has_two_decisions(game_data: dict[str, Any]) -> None:
    stations(game_data)["connect"]["decisions"].pop()
    assert "stations.connect.decisions: צריכים להיות לפחות 2 פריטים" in errors_of(game_data)


def test_decision_has_exactly_two_options(game_data: dict[str, Any]) -> None:
    options = stations(game_data)["connect"]["decisions"][0]["options"]
    options.append(options[0])
    assert "options: צריכים להיות לכל היותר 2 פריטים" in errors_of(game_data)


def test_tie_default_is_one_of_the_two_options(game_data: dict[str, Any]) -> None:
    stations(game_data)["connect"]["decisions"][0]["tie_default"] = 2
    assert "tie_default: צריך להיות לכל היותר 1" in errors_of(game_data)


def test_each_path_needs_outcome_and_analysis(game_data: dict[str, Any]) -> None:
    del stations(game_data)["connect"]["decisions"][1]["options"][0]["analysis"]
    assert "analysis: שדה חובה חסר" in errors_of(game_data)


def test_decision_ids_are_unique(game_data: dict[str, Any]) -> None:
    decisions = stations(game_data)["connect"]["decisions"]
    decisions[1]["id"] = decisions[0]["id"]
    assert "מזהה נקודת הכרעה 'd-hang' מופיע יותר מפעם אחת" in errors_of(game_data)


# ---------------------------------------------------------------- station 5


def test_crack_has_four_locks(game_data: dict[str, Any]) -> None:
    stations(game_data)["crack"]["locks"].pop()
    assert "stations.crack.locks: צריכים להיות לפחות 4 פריטים, ויש 3" in errors_of(game_data)


@pytest.mark.parametrize("field", ["hint", "token"])
def test_lock_needs_hint_and_token(game_data: dict[str, Any], field: str) -> None:
    del stations(game_data)["crack"]["locks"][2][field]
    assert f"stations.crack.locks[2].{field}: שדה חובה חסר" in errors_of(game_data)


def test_vault_needs_a_message(game_data: dict[str, Any]) -> None:
    stations(game_data)["crack"]["vault_message"] = " "
    assert "vault_message: לא יכול להיות ריק" in errors_of(game_data)


# ---------------------------------------------------------------- station 6


@pytest.mark.parametrize("round_index", range(3))
def test_championship_round_sizes(game_data: dict[str, Any], round_index: int) -> None:
    names = ["speed", "accuracy", "thinking"]
    name = names[round_index]
    expected = CHAMPIONSHIP_ROUNDS[round_index].questions
    stations(game_data)["championship"][name].pop()
    assert f"לפחות {expected} פריטים, ויש {expected - 1}" in errors_of(game_data)


# ---------------------------------------------------------------- station 7


def test_transfer_question_must_be_new(game_data: dict[str, Any]) -> None:
    transfer = stations(game_data)["seal"]["transfer_question"]
    transfer["text"] = game_data["anchor_question"]["text"] + "  "
    assert "שאלת ההעברה בתחנה 7 צריכה להיות חדשה" in errors_of(game_data)


@pytest.mark.parametrize("count", [2, 6])
def test_map_has_three_to_five_concepts(game_data: dict[str, Any], count: int) -> None:
    knowledge_map = stations(game_data)["seal"]["knowledge_map"]
    concepts = knowledge_map["concepts"]
    while len(concepts) < count:
        concepts.append({"id": f"c-extra-{len(concepts)}", "label": "מושג"})
    del concepts[count:]
    assert "concepts" in errors_of(game_data)


def test_map_central_concept_must_exist(game_data: dict[str, Any]) -> None:
    stations(game_data)["seal"]["knowledge_map"]["central"] = "c-missing"
    assert "המושג המרכזי 'c-missing' לא נמצא" in errors_of(game_data)


def test_map_links_must_point_to_concepts(game_data: dict[str, Any]) -> None:
    stations(game_data)["seal"]["knowledge_map"]["links"][0]["target"] = "c-missing"
    assert "מפנה למושג שלא קיים: 'c-missing'" in errors_of(game_data)


def test_map_link_cannot_loop_to_itself(game_data: dict[str, Any]) -> None:
    link = stations(game_data)["seal"]["knowledge_map"]["links"][0]
    link["target"] = link["source"]
    assert "לעצמו" in errors_of(game_data)


# ---------------------------------------------------------------- references and ids


def test_question_ids_are_unique_across_stations(game_data: dict[str, Any]) -> None:
    stations(game_data)["championship"]["speed"][0]["id"] = "q-anchor"
    assert "מזהה שאלה 'q-anchor' מופיע יותר מפעם אחת" in errors_of(game_data)


def test_confirm_question_ids_count_too(game_data: dict[str, Any]) -> None:
    stations(game_data)["crack"]["locks"][0]["confirm_question"]["id"] = "q-r1"
    assert "מזהה שאלה 'q-r1' מופיע יותר מפעם אחת" in errors_of(game_data)


def test_ids_use_a_safe_format(game_data: dict[str, Any]) -> None:
    stations(game_data)["championship"]["speed"][0]["id"] = "שאלה 1"
    assert "מזהה יכול לכלול רק" in errors_of(game_data)


def test_media_reference_must_exist(game_data: dict[str, Any]) -> None:
    stations(game_data)["connect"]["case"]["media_id"] = "m-missing"
    assert "הפניה למדיה שלא קיימת: 'm-missing'" in errors_of(game_data)


def test_question_media_reference_must_exist(game_data: dict[str, Any]) -> None:
    stations(game_data)["retrieve"]["recall"][0]["media_id"] = "m-missing"
    assert "הפניה למדיה שלא קיימת: 'm-missing'" in errors_of(game_data)


@pytest.mark.parametrize(
    "src", ["https://example.com/video.mp4", "/home/teacher/video.mp4", "../outside.mp4"]
)
def test_media_must_be_a_relative_file_in_the_package(game_data: dict[str, Any], src: str) -> None:
    game_data["media"][0]["src"] = src
    assert "נתיב יחסי בתוך החבילה" in errors_of(game_data)


def test_unknown_fields_are_rejected(game_data: dict[str, Any]) -> None:
    game_data["anchor_question"]["rationel"] = "שגיאת כתיב"
    assert "anchor_question.rationel: שדה לא מוכר" in errors_of(game_data)


def test_unknown_fields_in_a_station_are_rejected(game_data: dict[str, Any]) -> None:
    stations(game_data)["crack"]["lockz"] = []
    assert "stations.crack.lockz: שדה לא מוכר" in errors_of(game_data)


# ---------------------------------------------------------------- error formatting


def test_wrong_type_has_a_hebrew_message(game_data: dict[str, Any]) -> None:
    game_data["identity"]["grades"] = "fifth"
    assert "identity.grades: צריך להיות רשימה" in errors_of(game_data)


def test_unknown_error_types_fall_back_to_english(game_data: dict[str, Any]) -> None:
    game_data["identity"]["participants"] = 2.5
    assert "participants:" in errors_of(game_data)
