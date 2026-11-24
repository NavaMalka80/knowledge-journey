"""The template table itself must stay consistent."""

from knowledge_journey.template import (
    CHAMPIONSHIP_ROUNDS,
    KEY_TITLES,
    LOCK_TITLES,
    STATION_ORDER,
    STATION_RULES,
    TOTAL_SECONDS,
    VOTE_SECONDS,
    StationKind,
    VoteKind,
)


def test_durations_add_up_to_45_minutes() -> None:
    assert sum(r.duration_seconds for r in STATION_RULES.values()) == TOTAL_SECONDS


def test_every_station_has_a_rule_in_fixed_order() -> None:
    assert set(STATION_RULES) == set(StationKind)
    assert STATION_ORDER[0] is StationKind.SPARK
    assert STATION_ORDER[-1] is StationKind.SEAL


def test_championship_rounds_fill_the_station_and_score_160() -> None:
    assert sum(r.seconds for r in CHAMPIONSHIP_ROUNDS) == (
        STATION_RULES[StationKind.CHAMPIONSHIP].duration_seconds
    )
    assert sum(r.questions * r.points for r in CHAMPIONSHIP_ROUNDS) == 160


def test_every_vote_kind_has_a_default_time() -> None:
    assert set(VOTE_SECONDS) == set(VoteKind)


def test_three_keys_and_four_locks() -> None:
    assert len(KEY_TITLES) == 3
    assert len(LOCK_TITLES) == 4
