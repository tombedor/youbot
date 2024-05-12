# os.environ["OPENAI_BASE_URL"] = "http://localhost:1234/v1"
# os.environ["OPENAI_API_KEY"] = "lm-studio"
from dataclasses import dataclass
from datetime import datetime
import logging
import os
from time import sleep
from typing import List

from openai import OpenAI


client = OpenAI()
MODEL = client.models.list().data[0].id

MODEL = "gpt-3.5-turbo-instruct"
TEMPERATURE = 0.0
MAX_TOKENS = 2000

PKL_DIR = os.path.join(os.getcwd(), "__".join([MODEL, str(TEMPERATURE), str(MAX_TOKENS)]))

os.makedirs(PKL_DIR, exist_ok=True)


def get_openai_response(prompt: str) -> str:
    if MODEL.startswith("gpt-3.5"):
        sleep(0.1)
    if MODEL == "gpt-3.5-turbo-instruct":
        response = client.completions.create(model=MODEL, prompt=prompt, temperature=0.0, max_tokens=2000).choices[0].text
    else:
        response = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": prompt}]).choices[0].message.content

    assert response
    assert type(response) == str
    logging.info(f"Response: {response}")

    return response


VALID_RELATIONSHIPS = {
    ("PERSON", "PERSON"): [
        "IS_PLATONIC_FRIEND_TO",
        "IS_SIBLING_OF",
        "IS_PARENT_OF",
        "IS_EXTENDED_RELATIVE_OF",
        "IS_ROMANTIC_PARTNER_OF",
        "IS_COWORKER_OF",
        "FOLLOWS_IN_MEDIA",
        "IS_SAME_PERSON_AS",
    ],
    ("PERSON", "PET"): [
        "IS_PRIMARY_OWNER_OF",
        "TEMPORARILY_TOOK_CARE_OF",
    ],
    ("PERSON", "EVENT"): [
        "ATTENDED",
        "HOSTED",
    ],
    ("EVENT", "TIME"): ["OCCURRED_AT"],
    ("EVENT", "DATE"): ["OCCURED_ON"],
}


@dataclass
class Entity:
    name: str
    label: str
    confidence_score: float
    raw_facts: List[str]
    relationships: List["Relationship"]


@dataclass
class Person(Entity):
    first_name: str
    last_name: str
    birthday: datetime
    interests: List[str]
    is_public_figure: bool


@dataclass
class Pet(Entity):
    name: str
    species: str
    breed: str
    birthday: datetime
    interests: List[str]
    raw_facts: List[str]


class Relationship:
    from_entity: str
    to_entity: str

    is_reciprical: bool
    is_exclusive: bool


class RomanticRelationShip(Relationship):
    anniversary: datetime
    is_exclusive = True

    from_entity_types = [Person]
    to_entity_types = [Person]
