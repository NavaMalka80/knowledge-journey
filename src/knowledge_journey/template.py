"""The fixed seven-station template.

Every game passes through the same seven stations, in the same order, for a total
of 45 minutes. This module is the single place that describes the template, so a
change requested by the client (for example, how many riddles station 5 holds)
is a one-line change here.
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
    """What the template requires from one station.

    A count of ``None`` means "no rule yet": the requirements do not fix it.
    Question counts include the anchor question where it appears.
    """

    title: str
    duration_minutes: int
    knowledge: int | None = None
    questions: int | None = None
    min_questions: int = 0
    media: int | None = None
    has_anchor: bool = False


STATION_RULES: dict[StationKind, StationRule] = {
    StationKind.SPARK: StationRule("הניצוץ", 3, knowledge=0, questions=1, media=1, has_anchor=True),
    StationKind.DISCOVER: StationRule("מגלים", 7, knowledge=3),
    StationKind.RETRIEVE: StationRule("שולפים", 6, questions=6),
    StationKind.CONNECT: StationRule("מחברים", 9, questions=2, media=1),
    StationKind.CRACK: StationRule("מפצחים", 8, questions=4),
    # Three rounds (speed, accuracy, thinking); questions per round are still open.
    StationKind.CHAMPIONSHIP: StationRule("אליפות הידע", 8, min_questions=3),
    # The anchor question returns, plus one new transfer question.
    StationKind.SEAL: StationRule("חותם הידע", 4, questions=2, has_anchor=True),
}

STATION_ORDER: tuple[StationKind, ...] = tuple(StationKind)
TOTAL_MINUTES = 45
