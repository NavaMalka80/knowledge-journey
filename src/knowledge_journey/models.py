"""The data model of a Knowledge Journey game.

A game file (JSON) is loaded into these Pydantic models. Loading *is* validation:
if the file breaks a content rule from REQUIREMENTS section 5, loading fails with
a list of errors, long before the game reaches a classroom.

User-facing validation messages are in Hebrew, because teachers read them.
"""

from enum import StrEnum
from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from knowledge_journey.template import STATION_ORDER, STATION_RULES, StationKind

SCHEMA_VERSION: Literal[1] = 1

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Identifier = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=r"^[a-z0-9][a-z0-9-]*$")
]


class StrictModel(BaseModel):
    """Base for all models: unknown fields are errors, not silently ignored.

    A typo such as ``"rationel"`` must fail loudly instead of losing the rationale.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# ---------------------------------------------------------------- enums


class Mode(StrEnum):
    """How the session is used (REQUIREMENTS section 4)."""

    LEARNING = "learning"
    REVIEW = "review"


class ApprovalStatus(StrEnum):
    """Where the game stands in the teacher's workflow."""

    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class MediaKind(StrEnum):
    VIDEO = "video"
    IMAGE = "image"


# ---------------------------------------------------------------- building blocks


class LearningGoal(StrictModel):
    """A learning outcome that can be checked."""

    id: Identifier
    text: NonEmptyStr


class IdentityCard(StrictModel):
    """Who the game is for and what it should achieve.

    Feeds both the review agent and the facilitator guide.
    """

    subject: NonEmptyStr
    topic: NonEmptyStr
    age_min: int = Field(ge=3, le=120)
    age_max: int = Field(ge=3, le=120)
    grades: list[NonEmptyStr] = Field(min_length=1)
    mode: Mode
    prior_knowledge: str = ""
    learning_goals: list[LearningGoal] = Field(min_length=4, max_length=6)
    participants: int | None = Field(default=None, ge=1)
    notes: str = ""

    @model_validator(mode="after")
    def _check(self) -> "IdentityCard":
        if self.age_min > self.age_max:
            raise ValueError("גיל מינימלי גדול מגיל מקסימלי")
        _require_unique([g.id for g in self.learning_goals], "מזהה מטרת למידה")
        return self


class KnowledgeItem(StrictModel):
    """One concept presented on screen: a "knowledge key"."""

    id: Identifier
    concept: NonEmptyStr
    definition: NonEmptyStr
    example: NonEmptyStr
    goal_id: Identifier


class Question(StrictModel):
    """A multiple-choice question: four answers, exactly one correct, with a rationale.

    "Exactly one correct" holds by construction: the model stores a single index.
    """

    id: Identifier
    text: NonEmptyStr
    answers: list[NonEmptyStr] = Field(min_length=4, max_length=4)
    correct_index: int = Field(ge=0, le=3)
    rationale: NonEmptyStr
    difficulty: Difficulty = Difficulty.MEDIUM
    tags: list[NonEmptyStr] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check(self) -> "Question":
        normalized = [" ".join(a.split()) for a in self.answers]
        if len(set(normalized)) != len(normalized):
            raise ValueError("יש תשובות כפולות: כל ארבע התשובות צריכות להיות שונות")
        return self


class MediaItem(StrictModel):
    """A video or image file shipped inside the offline game package."""

    id: Identifier
    kind: MediaKind
    src: NonEmptyStr
    duration_seconds: int | None = Field(default=None, ge=1)
    captions: bool = False
    narration: bool = False
    version: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def _check(self) -> "MediaItem":
        # The player runs offline, so media must be a file inside the package.
        path = PurePosixPath(self.src)
        if "://" in self.src or path.is_absolute() or ".." in path.parts or "\\" in self.src:
            raise ValueError(
                "קובץ מדיה חייב להיות נתיב יחסי בתוך החבילה (למשל media/opening.mp4), "
                "ולא קישור לאינטרנט"
            )
        return self


# ---------------------------------------------------------------- steps


class KnowledgeStep(StrictModel):
    type: Literal["knowledge"] = "knowledge"
    item: KnowledgeItem


class QuestionStep(StrictModel):
    type: Literal["question"] = "question"
    question: Question


class MediaStep(StrictModel):
    type: Literal["media"] = "media"
    media_id: Identifier


class AnchorStep(StrictModel):
    """Shows the game's anchor question.

    The anchor is stored once, on the game, and stations 1 and 7 only point to it,
    so the two appearances cannot drift apart.
    """

    type: Literal["anchor"] = "anchor"


Step = Annotated[KnowledgeStep | QuestionStep | MediaStep | AnchorStep, Field(discriminator="type")]


class Station(StrictModel):
    kind: StationKind
    duration_minutes: int = Field(ge=1)
    steps: list[Step] = Field(min_length=1)

    def count(self, step_type: str) -> int:
        return sum(1 for step in self.steps if step.type == step_type)

    @model_validator(mode="after")
    def _check(self) -> "Station":
        """Apply the template rules for this kind of station."""
        rule = STATION_RULES[self.kind]
        name = f"תחנת {rule.title}"
        if self.duration_minutes != rule.duration_minutes:
            raise ValueError(f"{name}: המשך צריך להיות {rule.duration_minutes} דקות")

        anchors = self.count("anchor")
        if rule.has_anchor and anchors != 1:
            raise ValueError(f"{name}: צריכה להופיע בה שאלת העוגן, פעם אחת")
        if not rule.has_anchor and anchors:
            raise ValueError(f"{name}: שאלת העוגן מופיעה רק בתחנה 1 ובתחנה 7")

        questions = self.count("question") + anchors
        _check_count(name, "השאלות", questions, rule.questions)
        if questions < rule.min_questions:
            raise ValueError(f"{name}: צריכות להיות בה לפחות {rule.min_questions} שאלות")
        _check_count(name, "פריטי הידע", self.count("knowledge"), rule.knowledge)
        _check_count(name, "פריטי המדיה", self.count("media"), rule.media)
        return self


# ---------------------------------------------------------------- the game


class Game(StrictModel):
    """A complete game: identity card, key ideas and seven stations."""

    schema_version: Literal[1] = SCHEMA_VERSION
    title: NonEmptyStr
    version: int = Field(default=1, ge=1)
    status: ApprovalStatus = ApprovalStatus.DRAFT
    identity: IdentityCard
    key_ideas: list[NonEmptyStr] = Field(min_length=3, max_length=5)
    anchor_question: Question
    media: list[MediaItem] = Field(default_factory=list)
    stations: list[Station] = Field(min_length=7, max_length=7)

    def questions(self) -> list[Question]:
        """Every question in the game, the anchor first, each appearing once."""
        found = [self.anchor_question]
        for station in self.stations:
            found += [s.question for s in station.steps if isinstance(s, QuestionStep)]
        return found

    def knowledge_items(self) -> list[KnowledgeItem]:
        return [
            s.item
            for station in self.stations
            for s in station.steps
            if isinstance(s, KnowledgeStep)
        ]

    @model_validator(mode="after")
    def _check(self) -> "Game":
        kinds = tuple(station.kind for station in self.stations)
        if kinds != STATION_ORDER:
            order = ", ".join(STATION_RULES[k].title for k in STATION_ORDER)
            raise ValueError(f"התחנות צריכות להופיע בסדר הקבוע: {order}")

        _require_unique([q.id for q in self.questions()], "מזהה שאלה")
        _require_unique([k.id for k in self.knowledge_items()], "מזהה פריט ידע")
        _require_unique([m.id for m in self.media], "מזהה מדיה")

        goal_ids = {g.id for g in self.identity.learning_goals}
        for item in self.knowledge_items():
            if item.goal_id not in goal_ids:
                raise ValueError(f"פריט הידע '{item.id}' מפנה למטרה שלא קיימת: '{item.goal_id}'")

        media_ids = {m.id for m in self.media}
        for station in self.stations:
            for step in station.steps:
                if isinstance(step, MediaStep) and step.media_id not in media_ids:
                    raise ValueError(f"יש הפניה למדיה שלא קיימת: '{step.media_id}'")

        anchor = _normalize(self.anchor_question.text)
        seal = self.stations[-1]
        for step in seal.steps:
            if isinstance(step, QuestionStep) and _normalize(step.question.text) == anchor:
                raise ValueError("שאלת ההעברה בתחנה 7 צריכה להיות חדשה, ולא חזרה על שאלת העוגן")
        return self


# ---------------------------------------------------------------- helpers


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _require_unique(ids: list[str], label: str) -> None:
    seen: set[str] = set()
    for item_id in ids:
        if item_id in seen:
            raise ValueError(f"{label} '{item_id}' מופיע יותר מפעם אחת")
        seen.add(item_id)


def _check_count(name: str, label: str, actual: int, expected: int | None) -> None:
    if expected is not None and actual != expected:
        raise ValueError(f"{name}: מספר {label} צריך להיות {expected}, ויש {actual}")
