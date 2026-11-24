"""The data model of a Knowledge Journey game (schema version 2).

A game file (JSON) is loaded into these Pydantic models. Loading *is* validation:
if the file breaks a content rule, loading fails with a list of errors, long
before the game reaches a classroom.

Each of the seven stations has its own model with named fields, so the structure
itself guarantees the counts the template requires (three keys, four locks, and
so on). The numbers (times, points, thresholds) live in ``template.py``.

User-facing validation messages are in Hebrew, because teachers read them.
"""

from collections.abc import Iterator
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

SCHEMA_VERSION: Literal[2] = 2

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


class Theme(StrEnum):
    """The landscape "skin" of the game (ADR 0005)."""

    CITY = "city"
    FOREST = "forest"
    BEACH = "beach"
    DESERT = "desert"


# ---------------------------------------------------------------- building blocks


class LearningGoal(StrictModel):
    """A learning outcome that can be checked."""

    id: Identifier
    text: NonEmptyStr


class IdentityCard(StrictModel):
    """Who the game is for and what it should achieve.

    Feeds the review agent, the facilitator guide and the look of the game.
    """

    subject: NonEmptyStr
    topic: NonEmptyStr
    age_min: int = Field(ge=3, le=120)
    age_max: int = Field(ge=3, le=120)
    grades: list[NonEmptyStr] = Field(min_length=1)
    mode: Mode
    theme: Theme
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


class Content(StrictModel):
    """Something shown on screen: text, a media file, or both."""

    title: str = ""
    text: str = ""
    media_id: Identifier | None = None

    @model_validator(mode="after")
    def _check(self) -> "Content":
        if not self.text.strip() and self.media_id is None:
            raise ValueError("תוכן חייב לכלול טקסט, קובץ מדיה או את שניהם")
        return self


class Question(StrictModel):
    """A multiple-choice question: two to four answers, exactly one correct, with a rationale.

    "Exactly one correct" holds by construction: the model stores a single index.
    """

    id: Identifier
    text: NonEmptyStr
    answers: list[NonEmptyStr] = Field(min_length=2, max_length=4)
    correct_index: int = Field(ge=0, le=3)
    rationale: NonEmptyStr
    reinforcement: str = ""
    vote_seconds: int | None = Field(default=None, ge=5, le=300)
    media_id: Identifier | None = None
    difficulty: Difficulty = Difficulty.MEDIUM
    tags: list[NonEmptyStr] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check(self) -> "Question":
        if self.correct_index >= len(self.answers):
            raise ValueError(
                f"התשובה הנכונה (מספר {self.correct_index + 1}) לא קיימת: "
                f"יש רק {len(self.answers)} תשובות"
            )
        normalized = [_normalize(a) for a in self.answers]
        if len(set(normalized)) != len(normalized):
            raise ValueError("יש תשובות כפולות: כל התשובות צריכות להיות שונות")
        return self


# ---------------------------------------------------------------- station 1: הניצוץ


class SparkStation(StrictModel):
    """Opening video, the anchor question (stored on the game) and the opening goals."""

    opening_media_id: Identifier
    opening_goals: list[NonEmptyStr] = Field(min_length=2, max_length=3)


# ---------------------------------------------------------------- station 2: מגלים


class Key(StrictModel):
    """A knowledge key: short knowledge, a question, and help if the class gets it wrong.

    In learning mode the knowledge is shown before the question; in review mode after.
    """

    knowledge: Content
    examples: list[Content] = Field(default_factory=list, max_length=2)
    question: Question
    confirm_question: Question | None = None
    key_word: NonEmptyStr

    @model_validator(mode="after")
    def _check(self) -> "Key":
        if len(self.examples) == 1:
            raise ValueError("דוגמאות להבחנה מוצגות בזוג: צריך שתיים או אף אחת")
        if not self.question.reinforcement.strip():
            raise ValueError("לשאלת מפתח צריך הסבר חיזוק, למקרה שהכיתה טועה")
        return self


class DiscoverStation(StrictModel):
    identify: Key
    understand: Key
    distinguish: Key

    def all_keys(self) -> list[Key]:
        return [self.identify, self.understand, self.distinguish]


# ---------------------------------------------------------------- station 3: שולפים


class DistinguishTask(StrictModel):
    question: Question
    examples: list[Content] = Field(default_factory=list, max_length=2)

    @model_validator(mode="after")
    def _check(self) -> "DistinguishTask":
        if len(self.examples) == 1:
            raise ValueError("דוגמאות להבחנה מוצגות בזוג: צריך שתיים או אף אחת")
        return self


class ConnectTask(StrictModel):
    """Links a new concept to prior knowledge; the link is animated after the reveal."""

    question: Question
    new_concept: str = ""
    prior_concept: str = ""


class RetrieveStation(StrictModel):
    recall: list[Question] = Field(min_length=2, max_length=2)
    distinguish: list[DistinguishTask] = Field(min_length=2, max_length=2)
    connect: list[ConnectTask] = Field(min_length=2, max_length=2)


# ---------------------------------------------------------------- station 4: מחברים


class DecisionOption(StrictModel):
    """One path: what happened after the choice, and what it teaches."""

    label: NonEmptyStr
    outcome: Content
    analysis: Content


class Decision(StrictModel):
    """A decision point with exactly two options. A tie goes to ``tie_default``."""

    id: Identifier
    prompt: NonEmptyStr
    options: list[DecisionOption] = Field(min_length=2, max_length=2)
    tie_default: int = Field(default=0, ge=0, le=1)
    vote_seconds: int | None = Field(default=None, ge=5, le=300)


class ConnectStation(StrictModel):
    case: Content
    decisions: list[Decision] = Field(min_length=2, max_length=2)
    bridge: Content
    summary: Content

    @model_validator(mode="after")
    def _check(self) -> "ConnectStation":
        _require_unique([d.id for d in self.decisions], "מזהה נקודת הכרעה")
        return self


# ---------------------------------------------------------------- station 5: מפצחים


class Lock(StrictModel):
    """A knowledge lock. Opening it adds ``token`` to the vault code."""

    question: Question
    hint: NonEmptyStr
    confirm_question: Question | None = None
    token: NonEmptyStr


class CrackStation(StrictModel):
    locks: list[Lock] = Field(min_length=4, max_length=4)
    vault_message: NonEmptyStr


# ---------------------------------------------------------------- station 6: אליפות הידע


class ChampionshipStation(StrictModel):
    speed: list[Question] = Field(min_length=4, max_length=4)
    accuracy: list[Question] = Field(min_length=3, max_length=3)
    thinking: list[Question] = Field(min_length=2, max_length=2)


# ---------------------------------------------------------------- station 7: חותם הידע


class Concept(StrictModel):
    id: Identifier
    label: NonEmptyStr


class ConceptLink(StrictModel):
    source: Identifier
    target: Identifier
    label: str = ""


class KnowledgeMap(StrictModel):
    """The closing concept map. The teacher writes it; the player only draws it."""

    central: Identifier
    concepts: list[Concept] = Field(min_length=3, max_length=5)
    links: list[ConceptLink] = Field(min_length=1)
    principle: NonEmptyStr
    example: NonEmptyStr
    takeaway: NonEmptyStr

    @model_validator(mode="after")
    def _check(self) -> "KnowledgeMap":
        ids = [c.id for c in self.concepts]
        _require_unique(ids, "מזהה מושג")
        if self.central not in ids:
            raise ValueError(f"המושג המרכזי '{self.central}' לא נמצא ברשימת המושגים")
        for link in self.links:
            for end in (link.source, link.target):
                if end not in ids:
                    raise ValueError(f"קשר במפת הידע מפנה למושג שלא קיים: '{end}'")
            if link.source == link.target:
                raise ValueError(f"קשר במפת הידע מחבר את '{link.source}' לעצמו")
        return self


class SealStation(StrictModel):
    """The anchor returns (stored on the game), then a transfer question and the map."""

    transfer_question: Question
    knowledge_map: KnowledgeMap
    closing_message: str = ""


# ---------------------------------------------------------------- the game


class Stations(StrictModel):
    """The seven stations. Named fields, so the fixed order cannot be broken."""

    spark: SparkStation
    discover: DiscoverStation
    retrieve: RetrieveStation
    connect: ConnectStation
    crack: CrackStation
    championship: ChampionshipStation
    seal: SealStation


class Game(StrictModel):
    """A complete game: identity card, key ideas, the anchor question and seven stations."""

    schema_version: Literal[2] = SCHEMA_VERSION
    title: NonEmptyStr
    version: int = Field(default=1, ge=1)
    status: ApprovalStatus = ApprovalStatus.DRAFT
    identity: IdentityCard
    key_ideas: list[NonEmptyStr] = Field(min_length=3, max_length=5)
    anchor_question: Question
    media: list[MediaItem] = Field(default_factory=list)
    stations: Stations

    def questions(self) -> list[Question]:
        """Every question in the game, the anchor first, each appearing once."""
        return list(self._iter_questions())

    def _iter_questions(self) -> Iterator[Question]:
        s = self.stations
        yield self.anchor_question
        for key in s.discover.all_keys():
            yield key.question
            if key.confirm_question:
                yield key.confirm_question
        yield from s.retrieve.recall
        yield from (t.question for t in s.retrieve.distinguish)
        yield from (t.question for t in s.retrieve.connect)
        for lock in s.crack.locks:
            yield lock.question
            if lock.confirm_question:
                yield lock.confirm_question
        yield from s.championship.speed
        yield from s.championship.accuracy
        yield from s.championship.thinking
        yield s.seal.transfer_question

    def _media_refs(self) -> Iterator[tuple[str, MediaKind | None]]:
        """Every media reference, with the kind it must be (None: any kind)."""
        s = self.stations
        yield s.spark.opening_media_id, MediaKind.VIDEO
        contents: list[Content] = []
        for key in s.discover.all_keys():
            contents += [key.knowledge, *key.examples]
        for task in s.retrieve.distinguish:
            contents += task.examples
        contents += [s.connect.case, s.connect.bridge, s.connect.summary]
        for decision in s.connect.decisions:
            for option in decision.options:
                contents += [option.outcome, option.analysis]
        for content in contents:
            if content.media_id:
                yield content.media_id, None
        for question in self.questions():
            if question.media_id:
                yield question.media_id, None

    @model_validator(mode="after")
    def _check(self) -> "Game":
        _require_unique([q.id for q in self.questions()], "מזהה שאלה")
        _require_unique([m.id for m in self.media], "מזהה מדיה")

        kinds = {m.id: m.kind for m in self.media}
        for media_id, required in self._media_refs():
            if media_id not in kinds:
                raise ValueError(f"יש הפניה למדיה שלא קיימת: '{media_id}'")
            if required is not None and kinds[media_id] != required:
                raise ValueError(f"'{media_id}' צריך להיות סרטון")

        transfer = self.stations.seal.transfer_question
        if _normalize(transfer.text) == _normalize(self.anchor_question.text):
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
