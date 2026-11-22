"""The template table itself must stay consistent."""

from knowledge_journey.template import STATION_ORDER, STATION_RULES, TOTAL_MINUTES, StationKind


def test_durations_add_up_to_45_minutes() -> None:
    assert sum(r.duration_minutes for r in STATION_RULES.values()) == TOTAL_MINUTES


def test_every_station_has_a_rule() -> None:
    assert set(STATION_RULES) == set(StationKind)
    assert len(STATION_ORDER) == 7


def test_anchor_appears_only_in_first_and_last_station() -> None:
    with_anchor = [k for k in STATION_ORDER if STATION_RULES[k].has_anchor]
    assert with_anchor == [StationKind.SPARK, StationKind.SEAL]
