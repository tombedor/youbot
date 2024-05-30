from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from typing import List, Optional, Tuple

from tqdm import tqdm


from youbot.clients.llm_client import query_llm, query_llm_json

TRUST_LABELS = ["CARDINAL", "DATE", "TIME"]


class EntityLabel(Enum):
    UNKNOWN = 0
    PRIMARY_USER = 1
    PERSON = 2
    PET = 3
    ORG = 4
    PRODUCT = 5
    WEBSITE = 6
    GPE = 7
    TVSHOW = 8
    BOOK = 9
    MOVIE = 10
    TECHNICAL_CONCEPT = 11
    MUSICAL_GROUP = 12
    EVENT = 13
    # skippable
    CARDINAL = 14
    DATE = 15
    TIME = 16
    AI_ASSISTANT = 17
    PROJECT = 18


VALID_LABELS = [k for k in EntityLabel.__members__.keys() if k != "PRIMARY_USER"]


@dataclass
class Entity:
    entity_name: str
    entity_label = EntityLabel.UNKNOWN
    facts: set[str] = field(default_factory=set)
    summary: Optional[str] = None

    def description(self):
        # attribute_kvs = ""
        # for k in self.llm_short_editable_attributes():
        #     v = getattr(self, k)
        #     if not v:
        #         val = "?"
        #     else:
        #         val = v
        #     attribute_kvs += f"{k}: {val}\n"

        return f"""
The entity named {self.entity_name} is of type {self.entity_label.name}. A summary:

{self.summary}
"""

    def llm_short_editable_attributes(self) -> Tuple[str]:
        items = [k for k in self.__dict__.keys() if k not in ["entity_label", "entity_name", "facts", "summary"]]
        items.sort()
        return tuple(items)  # type: ignore

    def summary_prompt(self) -> Optional[str]:
        return None

    def determine_attributes(self):
        # attrs_to_facts = {}

        # for fact in tqdm(self.facts, f"determine facts which apply to entity {self.entity_name}"):
        #     attrs = determine_relevant_attributes_for_entity(
        #         self.entity_name, self.entity_label.name, fact, self.llm_short_editable_attributes()
        #     )
        #     for attr in attrs:
        #         attrs_to_facts[attr] = attrs_to_facts.get(attr, set())
        #         attrs_to_facts[attr].add(fact)

        # for attr, facts in attrs_to_facts.items():
        #     logging.info("Found %s facts relevant to attribute %s", len(facts), attr)
        #     facts_list = list(facts)
        #     facts_list.sort()
        #     value = determine_attribute_value_for_entity(self.entity_name, self.entity_label.name, attr, tuple(facts_list))
        #     if value:
        #         setattr(self, attr, value)

        if self.summary_prompt():
            self.summary = summarize_known_information(entity_name=self.entity_name, entity_type=self.entity_label.name, summary_prompt=self.summary_prompt(), facts=tuple(self.facts))  # type: ignore


@dataclass
class Event(Entity):
    entity_label = EntityLabel.EVENT
    name: Optional[str] = None
    date: Optional[datetime] = None
    location: Optional[str] = None

    def summary_prompt(self) -> Optional[str]:
        return "Summarize the event, including the date, location, and a brief description of the event."


class Project(Entity):
    entity_label = EntityLabel.PROJECT

    def summary_prompt(self) -> Optional[str]:
        return "Summarize the project, including the description, who is working on it, what the goal is, and current status."


class Movie(Entity):
    entity_label = EntityLabel.MOVIE

    def summary_prompt(self) -> Optional[str]:
        return "Briefly summarize the movie, including the plot, main characters, and any notable aspects. Also note how the primary user relates to the movie."


@dataclass
class Person(Entity):
    entity_label = EntityLabel.PERSON
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birthday: Optional[datetime] = None
    occupation: Optional[str] = None
    relation_to_primary_user: Optional[str] = None

    def summary_prompt(self) -> Optional[str]:
        return "Summarize the personal and professional life of this person. Discuss likes and dislikes, what is important to them, and their relationships with others."

    # likes: Optional[str] = None
    # dislikes: Optional[str] = None


@dataclass
class PrimaryUser(Person):
    entity_label = EntityLabel.PRIMARY_USER
    relation_to_primary_user = "self"

    def llm_short_editable_attributes(self) -> Tuple[str]:
        return tuple(k for k in super().llm_short_editable_attributes() if k != "relation_to_primary_user")  # type: ignore

    def summary_prompt(self) -> Optional[str]:
        return """
Summarize the personal and professional life of this person. Discuss likes and dislikes, what is important to them, and their relationships with others.
As this is the primary user of an AI personal assistant, also discuss their attitudes towards AI personal assistants"""


@dataclass
class Pet(Entity):
    entity_label = EntityLabel.PET
    name: Optional[str] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    birthday: Optional[datetime] = None
    relation_to_primary_user: Optional[str] = None

    def __post_init__(self):
        self.name = self.entity_name

    def llm_short_editable_attributes(self) -> Tuple[str]:
        return tuple(k for k in super().llm_short_editable_attributes() if k != "name")  # type: ignore

    def summary_prompt(self) -> Optional[str]:
        return "Summarize what you know about this pet. Discuss things they like, things they dislike, and things about their behavior and care."


CONFIDENCE_THRESHOLD = 0.7


def determine_relevant_attributes_for_entity(entity_name: str, entity_label: str, fact: str, attributes: Tuple[str]) -> List[str]:

    attr_str = ", ".join(attributes)
    prompt: str = f"""There is an entity that we have incomplete information about.
        Given a fact, determine which attribute could be updated based on the fact.
        Do not provide the value of the attribute, merely identify which attribute or attributes could be updated.
        
        The entity is named {entity_name} and is of type {entity_label}
        The attribute choices are {attr_str}. Your answer MUST be one or more of these attributes.
        
        The fact is: {fact}
        
        Your answer MUST be in json mode. The response should have the following keys:
        ATTRIBUTE_NAME: The attribute name you are updating
        REASON: A short explanation of why you chose this attribute
        
        If you believe multiple attributes could be updated, provide multiple responses in a list.
        
        If you believe no attributes match, return NONE as the attribute name.
        """
    response = query_llm_json(prompt)

    if "ATTRIBUTE_NAME" in response:
        if type(response["ATTRIBUTE_NAME"]) == str:  # type: ignore
            attrs = [response["ATTRIBUTE_NAME"]]  # type: ignore
        elif type(response["ATTRIBUTE_NAME"]) == list:  # type: ignore
            attrs = response["ATTRIBUTE_NAME"]  # type: ignore
        else:
            raise ValueError(f"Invalid response format: {response}")
    elif type(response) == dict:
        vals = list(response.values())
        if len(vals) == 1 and type(vals[0]) == list:  # type: ignore
            attrs = [r["ATTRIBUTE_NAME"] for r in vals[0]]  # type: ignore
        else:
            raise ValueError(f"Invalid response format: {response}")
    elif type(response) == list:
        attrs = [r["ATTRIBUTE_NAME"] for r in response]
    else:
        raise ValueError(f"Invalid response format: {response}")

    valid_answers = []
    for attr in attrs:
        if attr in attributes:
            valid_answers.append(attr)
        else:
            logging.error("Invalid attribute name: %s", attr)

    return valid_answers


def determine_attribute_value_for_entity(entity_name: str, entity_label: str, attribute_name: str, facts: Tuple[str]) -> Optional[str]:
    value_to_score = {}
    total_score = 0
    for fact in tqdm(facts, f"determining {attribute_name} for entity {entity_name}"):
        prompt = f"""There is an entity that we have incomplete information about.
            Given a fact and an attribute, determine the value of the attribute based on the fact.
            
            The entity is named {entity_name} and is of type {entity_label}
            The attribute is {attribute_name}
            
            The fact is: {fact}
            
            Provide an answer in JSON format. Your response should have the following keys:
            ATTRIBUTE_VALUE: The new value for the attribute
            CONFIDENCE_SCORE: A value from 1-100, where 100 is more confident and 0 is least
            REASON: A short explanation of why you chose this value
            """

        response = query_llm_json(prompt)
        value = response["ATTRIBUTE_VALUE"]  # type: ignore
        confidence_score = response["CONFIDENCE_SCORE"]  # type: ignore
        total_score += confidence_score

        if type(value) == list:
            value.sort()
            value_str = ", ".join(value)
        elif type(value) == str:
            value_str = value
        else:
            raise ValueError(f"Invalid value type: {type(value)}. Value = {value}")

        value_to_score[value_str] = value_to_score.get(value_str, 0) + confidence_score

    winning_score = float("-inf")
    winning_value = None
    for value, score in value_to_score.items():
        if score > winning_score:
            winning_value = value
    logging.info("Winning value for attribute %s is %s", attribute_name, winning_value)
    return winning_value


def summarize_known_information(entity_name: str, entity_type: str, summary_prompt: str, facts: Tuple[str]) -> str:
    facts_list = list(facts)
    facts_list.sort()
    facts_str = "\n".join(facts_list)

    prompt = f"""
        {summary_prompt}
        
        The entity is named {entity_name} and is of type {entity_type}
        
        The facts are:
        {facts_str}
        
        
        Your answer should be a summary of the known information about {entity_name}
        """

    response = query_llm(prompt)
    assert response
    return response


def calculate_label_for_entity_name(entity_name: str, facts: Tuple[str], prior_label: Optional[str] = None) -> Optional[str]:
    if prior_label and prior_label in TRUST_LABELS:
        return prior_label

    if entity_name == "Tom":
        return EntityLabel.PRIMARY_USER.name

    if entity_name == "Sam":
        return EntityLabel.AI_ASSISTANT.name

    total_score = 0
    label_candidates_to_score = {}
    for fact in facts:

        labels_str = ", ".join(VALID_LABELS)

        prompt = f"""You are an entity resolution assistant. 
            You must classify the entity with name = {entity_name}
            
            The valid choices are: {labels_str}
            
            
            Use both your inherent knowledge, and this facts derived from chat logs:
            {fact}
            
            Your response should be in JSON format, with the following keys:
            LABEL: The label you choos. Must be from list of choices: {labels_str}
            CONFIDENCE_SCORE: A value from 1-100, where 100 is more confident and 0 is least
            REASONING: A short explanation of why you chose this label
            """
        response = query_llm_json(prompt)
        confidence_score = response["CONFIDENCE_SCORE"]  # type: ignore
        label = response["LABEL"]  # type: ignore

        total_score += confidence_score
        label_candidates_to_score[label] = label_candidates_to_score.get(label, 0) + confidence_score

    winning_score = float("-inf")
    winning_label = None
    for label, score in label_candidates_to_score.items():
        if score > winning_score:
            winning_label = label
    return winning_label
