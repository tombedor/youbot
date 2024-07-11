from dataclasses import dataclass
import logging
from typing import List, Set
from youbot.data_models import VALID_LABELS, Entity, EntityLabel, Fact
from youbot.clients.llm_client import query_llm, query_llm_json
from youbot.memory.archival_facts import get_archival_memory_facts
from youbot.memory.google_calendar_facts import get_calendar_facts
from youbot.store import upsert_memory_entity
from toolz import pipe, concat, concatv
from toolz.curried import map, remove
from toolz.itertoolz import reduceby


@dataclass
class EntFact:
    """Utility data class, intermediate for knowledge processing"""

    youbot_user_id: int
    entity_name: str
    entity_label: EntityLabel
    fact: str


def refresh_knowledge(youbot_user_id: int) -> None:
    pipe(
        concatv(get_archival_memory_facts(youbot_user_id), get_calendar_facts(youbot_user_id)),
        map(calculate_ent_fact),
        concat,
        lambda ent_facts: reduceby(
            lambda x: (x.entity_name, x.entity_label), lambda acc, x: concatv(acc, [x.fact]), ent_facts, init=list  # type: ignore
        ),  # collect the list of facts that applies to each entity
        lambda _dict: [(k[0], k[1], set(v)) for k, v in _dict.items()],  # entity_name, entity_label, facts
        remove(lambda _: _[1].summary_prompt is None),  # not all entities need to be persisted into memory.
        list,
        map(lambda _: calculate_entity(*_)),
        map(upsert_memory_entity(youbot_user_id)),
        list,
    )


def calculate_ent_fact(fact: Fact) -> List[EntFact]:
    assert isinstance(fact, Fact)
    labels_str = ", ".join(VALID_LABELS)
    return pipe(
        query_llm_json(
            prompt=fact.text,
            system=f"""
        You are an entity resolution assistant. Given a fact, output a list of entities, their labels, and your reasoning.
        Your response should be a JSON formatted list, with the following format:
        ENTITY_NAME: The name of the entity
        ENTITY_LABEL: The label you choose for the entity. Must be from list of choices: {labels_str}
        REASONING: A short explanation of why you chose this label
        
        The list should be nested under a key called ENTITIES.
        
        For non-date entities, focus on specific entities. Ignore general entities like "a project" or "place". 
        Also ignore generic placeholder entities like "foobar" or "my_project".
        """,
        ),
        # debug,
        lambda _: _["ENTITIES"],
        map(
            lambda x: (
                EntFact(
                    youbot_user_id=fact.youbot_user_id,
                    entity_name=x["ENTITY_NAME"],
                    entity_label=EntityLabel[x["ENTITY_LABEL"]],
                    fact=fact.text,
                )
                if x["ENTITY_LABEL"] in EntityLabel.__members__
                else logging.warn(f"Skipping entity with name {x['ENTITY_NAME']} and invalid label {x['ENTITY_LABEL']}")
            )
        ),
        remove(lambda _: _ is None),
        list,
    )  # type: ignore


def calculate_entity(entity_name: str, entity_label: EntityLabel, facts: Set[str]) -> Entity:
    return pipe(
        facts,
        list,
        sorted,  # sort to ensure cache hits for same input
        lambda _: concatv([f"Entity name: {entity_name}. Entity Label: {entity_label.name}"], _),
        "\n".join,
        lambda _: query_llm(prompt=_, system=entity_label.summary_prompt),
        lambda _: Entity(entity_name=entity_name, entity_label=entity_label, summary=_, facts=facts),
    )
