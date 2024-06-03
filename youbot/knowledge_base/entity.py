from dataclasses import dataclass
from typing import Optional

TRUST_LABELS = ["CARDINAL", "DATE", "TIME"]

import enum


class EntityLabel(enum.Enum):

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, summary_prompt: Optional[str]):
        self.summary_prompt = summary_prompt

    UNKNOWN = None
    PRIMARY_USER = "Summarize the personal and professional life of this person. Discuss likes and dislikes, what is important to them, and their relationships with others. As this is the primary user of an AI personal assistant, also discuss their attitudes towards AI personal assistants"
    PERSON = "Summarize the personal and professional life of this person. Discuss likes and dislikes, what is important to them, and their relationships with others."
    PET = "Summarize what you know about this pet. Discuss things they like, things they dislike, and things about their behavior and care."
    ORG = None
    PRODUCT = None
    WEBSITE = None
    GPE = None
    TVSHOW = None
    BOOK = None
    MOVIE = "Briefly summarize the movie, including the plot, main characters, and any notable aspects. Also note how the primary user relates to the movie."
    TECHNICAL_CONCEPT = None
    MUSICAL_GROUP = (
        "Summarize the musical group, including the members, genre, and notable songs. Discuss how the primary user feels about the group."
    )
    EVENT = "Summarize the event, including the date, location, and a brief description of the event."
    # skippable
    CARDINAL = None
    DATE = None
    TIME = None
    AI_ASSISTANT = None
    PROJECT = "Summarize the project, including the description, who is working on it, what the goal is, and current status."


VALID_LABELS = [k for k in EntityLabel.__members__.keys() if k != EntityLabel.PRIMARY_USER.name]


@dataclass
class Entity:
    entity_name: str
    entity_label: EntityLabel
    facts: set[str]
    summary: str
