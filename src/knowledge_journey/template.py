"""The fixed seven-station template and its default values.

Every game passes through the same seven stations, in the same order, for a total
of 45 minutes. The *structure* of each station lives in ``models.py``; this module
holds the *numbers*: time budgets, voting times, scoring and thresholds.

All of these are proposed defaults from the client's specification and still await
final approval (ADR 0004), so they are kept here, in one place, to be easy to change.
"""

from dataclasses import dataclass
from enum import StrEnum


class StationKind(StrEnum):
    """The seven stations, in their fixed order."""

    SPARK = "spark"  # 1. הניצוץ
    DISCOVER = "discover"  # 2. מגלים
    RETRIEVE = "retrieve"  # 3. שולפים
    CONNECT = "connect"  # 4. מחברים
    CRACK = "crack"  # 5. מפצחים
    CHAMPIONSHIP = "championship"  # 6. אליפות הידע
    SEAL = "seal"  # 7. חותם הידע


@dataclass(frozen=True)
class StationRule:
    title: str
    duration_seconds: int


STATION_RULES: dict[StationKind, StationRule] = {
    StationKind.SPARK: StationRule("הניצוץ", 180),
    StationKind.DISCOVER: StationRule("מגלים", 420),
    StationKind.RETRIEVE: StationRule("שולפים", 360),
    StationKind.CONNECT: StationRule("מחברים", 540),
    StationKind.CRACK: StationRule("מפצחים", 480),
    StationKind.CHAMPIONSHIP: StationRule("אליפות הידע", 480),
    StationKind.SEAL: StationRule("חותם הידע", 240),
}

STATION_ORDER: tuple[StationKind, ...] = tuple(StationKind)
TOTAL_SECONDS = 45 * 60


class VoteKind(StrEnum):
    """Kinds of vote, each with its own default voting time."""

    RECALL = "recall"
    DISTINGUISH = "distinguish"
    CASE = "case"
    LOCK = "lock"
    SPEED = "speed"
    ACCURACY = "accuracy"
    THINKING = "thinking"


# Default voting time in seconds. A question may override it with ``vote_seconds``.
# Where the specification gives a range, the upper bound is used.
VOTE_SECONDS: dict[VoteKind, int] = {
    VoteKind.RECALL: 20,
    VoteKind.DISTINGUISH: 30,
    VoteKind.CASE: 45,
    VoteKind.LOCK: 30,
    VoteKind.SPEED: 10,
    VoteKind.ACCURACY: 25,
    VoteKind.THINKING: 45,
}


@dataclass(frozen=True)
class ChampionshipRound:
    title: str
    questions: int
    seconds: int
    points: int
    vote: VoteKind


CHAMPIONSHIP_ROUNDS: tuple[ChampionshipRound, ...] = (
    ChampionshipRound("מהירות", 4, 120, 10, VoteKind.SPEED),
    ChampionshipRound("דיוק", 3, 180, 20, VoteKind.ACCURACY),
    ChampionshipRound("חשיבה", 2, 180, 30, VoteKind.THINKING),
)

# Names of the three keys (station 2) and the four locks (station 5), in order.
KEY_TITLES: tuple[str, ...] = ("מזהים", "מבינים", "מבחינים")
LOCK_TITLES: tuple[str, ...] = ("מנעול הזיהוי", "מנעול הדיוק", "מנעול היישום", "מנעול הפיצוח")

# Show the extended reinforcement when fewer than this share of votes were correct.
REINFORCEMENT_THRESHOLD = 0.70
