from dataclasses import dataclass
from datetime import UTC, datetime
import enum
import re
from typing import List, Optional
from uuid import UUID
from pydantic import field_validator
import pytz
from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field


@dataclass
class Fact:
    youbot_user_id: int
    text: str
    timestamp: datetime


class Signup(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int = Field(..., description="The unique identifier for the user", primary_key=True, index=True)
    created_at: datetime = Field(default=datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    name: str = Field(..., description="The name of the user")
    phone: Optional[str] = Field(None, description="The phone number for the user")
    email: Optional[str] = Field(None, description="The email for the user")


class YoubotUser(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int = Field(..., description="The unique identifier for the user", primary_key=True, index=True)
    created_at: datetime = Field(default=datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    name: str = Field(..., description="The name of the user")
    memgpt_user_id: UUID = Field(..., description="The unique identifier for the user in the memgpt system")
    memgpt_agent_id: UUID = Field(..., description="The unique identifier for the user's agent in the memgpt system")
    phone: Optional[str] = Field(str, description="The phone number for the user")
    email: Optional[str] = Field(..., description="The email for the user")

    @field_validator("phone")
    def phone_is_e164(cls, phone: str) -> str:
        if not bool(re.match(r"^\+\d{1,15}$", phone)):
            raise ValueError("Invalid phone number format")
        return phone


class SmsWebhookLog(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int = Field(..., description="The unique identifier for the user", primary_key=True, index=True)
    created_at: datetime = Field(default=datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    source: str = Field(..., description="Where the webhook came from")
    info: str = Field(..., description="The information from the webhook")


class AgentReminder(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int = Field(..., description="The unique identifier for the user", primary_key=True, index=True)
    created_at: datetime = Field(default=datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    youbot_user_id: int = Field(..., description="Youbot user whose assistant is being reminded")
    state: str = Field("pending", description="The state of the reminder")
    reminder_time_utc: datetime = Field(..., description="Time to remind the user")
    reminder_message: str = Field(..., description="Message to remind the agent with")


class MemoryEntity(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int = Field(..., description="The unique identifier for the user", primary_key=True, index=True)
    created_at: datetime = Field(default=datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    youbot_user_id: int = Field(..., description="Youbot user whose assistant is being reminded")
    entity_name: str = Field(..., description="The name of the entity")
    entity_label: str = Field(..., description="The label of the entity")
    text: str = Field(..., description="The text of the entity")
    UniqueConstraint("youbot_user_id", "entity_name", "entity_label")
    # embedding = mapped_column(Vector(MAX_EMBEDDING_DIM))
    # embedding_dim: int = Field(..., description="The dimension of the embedding")
    # embedding_model: str = Field(..., description="The model used to generate the embedding")


class CalendarEventDB(SQLModel, table=True):
    id: int = Field(..., description="The unique identifier for the user", primary_key=True, index=True)
    youbot_user_id: int
    event_id: str
    summary: str
    description: Optional[str]
    start: datetime
    end: datetime
    location: Optional[str]
    attendee_emails: str  # csv
    recurrence: str  # csv
    reminders: bool
    visibility: str
    UniqueConstraint("event_id", "youbot_user_id")


@dataclass
class CalendarEvent:
    event_id: str
    summary: str
    description: Optional[str]
    start: datetime
    end: datetime
    location: Optional[str]
    attendee_emails: List[str]
    recurrence: List[str]
    reminders: bool
    visibility: str

    def __post_init__(self):
        self.start = convert_to_utc(self.start)
        self.end = convert_to_utc(self.end)


def convert_to_utc(dt: datetime) -> datetime:
    """Convert a datetime object to UTC if it contains time; leave date-only as naive."""
    if dt.tzinfo is None:
        return pytz.utc.localize(dt)
    else:
        return dt.astimezone(pytz.UTC)


TRUST_LABELS = ["CARDINAL", "DATE", "TIME"]


class EntityLabel(enum.Enum):
    GENERAL_GUIDANCE = """ Do not speculate, base your description strictly on the provided information. Focus on how the entity is relevant to the primary user."""

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, summary_prompt: Optional[str]):
        self.summary_prompt = summary_prompt

    UNKNOWN = None
    PRIMARY_USER = "Summarize the personal and professional life of this person. Discuss likes and dislikes, what is important to them, and their relationships with others. As this is the primary user of an AI personal assistant, also discuss their attitudes towards AI personal assistants."
    PERSON = "Summarize the personal and professional life of this person. Discuss likes and dislikes, what is important to them, and their relationships with others." + GENERAL_GUIDANCE  # type: ignore
    PET = "Summarize what you know about this pet. Discuss things they like, things they dislike, and things about their behavior and care." + GENERAL_GUIDANCE  # type: ignore
    ORG = None
    PRODUCT = None
    WEBSITE = None
    GPE = None
    TVSHOW = None
    BOOK = None
    MOVIE = "Briefly summarize the movie, including the plot, main characters, and any notable aspects." + GENERAL_GUIDANCE  # type: ignore
    TECHNICAL_CONCEPT = None
    MUSICAL_GROUP = (
        "Summarize the musical group, including the members, genre, and notable songs. Discuss how the primary user feels about the group."
    )
    EVENT = "Summarize the event, including the date, location, and a brief description of the event." + GENERAL_GUIDANCE  # type: ignore
    # skippable
    CARDINAL = None
    DATE = "Summarize information about this date, including any signficant events relating to the primary user. Do not include information exclusively about chats between the AI and the user. Instead, focus on the contents of the chats. " + GENERAL_GUIDANCE  # type: ignore
    TIME = None
    AI_ASSISTANT = None
    PROJECT = "Summarize the project, including the description, who is working on it, what the goal is, and current status." + GENERAL_GUIDANCE  # type: ignore


VALID_LABELS = [k for k in EntityLabel.__members__.keys() if k != EntityLabel.PRIMARY_USER.name]


@dataclass
class Entity:
    entity_name: str
    entity_label: EntityLabel
    facts: set[str]
    summary: str
