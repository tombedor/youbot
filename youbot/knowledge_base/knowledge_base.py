from dataclasses import dataclass
import logging
import pickle
from typing import Generator, List, Optional, Set
import spacy
from spacy.tokens.doc import Doc
from tqdm import tqdm
import youbot
from youbot.data_models import YoubotUser
from youbot.clients.llm_client import query_llm, query_llm_json
from youbot.knowledge_base.entity import (
    TRUST_LABELS,
    VALID_LABELS,
    Entity,
    EntityLabel,
)
from youbot.store import get_archival_messages, get_youbot_user_by_id, upsert_memory_entity
from memgpt.agent_store.storage import ArchivalMemoryModel

MODELS = ["gpt-3.5-turbo-0125", "gpt-3.5-turbo-instruct", "gpt-4o"]


class NLP:
    """Wrapping in a class prevent unnecessary loading of the model."""

    pipeline = None

    @classmethod
    def process(cls, text: str) -> Doc:
        if cls.pipeline is None:
            cls.pipeline = spacy.load("en_core_web_md")
        return cls.pipeline(text)


@dataclass
class PrecursorEntFacts:
    youbot_user: YoubotUser
    entity_name: str
    facts: Set[str]
    initial_labels: Set[str]


def calculate_ents_facts(youbot_user: YoubotUser, archival_messages: List[ArchivalMemoryModel]) -> List[PrecursorEntFacts]:
    names_to_facts = {}
    names_to_labels = {}

    for archival_msg in archival_messages:
        enriched_doc = NLP.process(archival_msg.text)  # type: ignore
        for ent in enriched_doc.ents:
            names_to_facts.setdefault(ent.text, set()).add(archival_msg.text)
            names_to_labels.setdefault(ent.text, set()).add(ent.label_)
    ent_facts = []
    for name in names_to_facts.keys():
        ent_facts.append(
            PrecursorEntFacts(youbot_user=youbot_user, entity_name=name, facts=names_to_facts[name], initial_labels=names_to_labels[name])
        )

    return ent_facts


def calculate_label_for_entity_name(ent_facts: PrecursorEntFacts) -> EntityLabel:
    ent_label = None

    if len(ent_facts.initial_labels) == 1 and list(ent_facts.initial_labels)[0] in TRUST_LABELS:
        label = list(ent_facts.initial_labels)[0]
        return EntityLabel[label]
    elif ent_facts.entity_name == "Tom":
        return EntityLabel.PRIMARY_USER
    elif ent_facts.entity_name == "Sam":
        return EntityLabel.AI_ASSISTANT
    else:
        total_score = 0
        label_candidates_to_score = {}
        for fact in ent_facts.facts:

            labels_str = ", ".join(VALID_LABELS)

            prompt = f"""You are an entity resolution assistant. 
                You must classify the entity with name = {ent_facts.entity_name}
                
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
        return EntityLabel[winning_label]  # type: ignore


def summarize_known_information(entity_name: str, entity_label: EntityLabel, facts: Set[str]) -> str:
    raw_facts_list = list(facts)
    raw_facts_list.sort()
    facts_list = [f"Entity name: {entity_name}. Entity Label: {entity_label.name}"]
    summary_prompt = entity_label.summary_prompt

    response = query_llm(prompt="\n".join(facts_list), system=summary_prompt)
    assert response
    return response


def calculate_entity(ent_fact: PrecursorEntFacts) -> Optional[Entity]:
    label = calculate_label_for_entity_name(ent_fact)
    logging.debug(f"Label for {ent_fact.entity_name} is {label.name}")
    if label.summary_prompt is not None:
        logging.debug("calculating entity summary")
        entity_summary = summarize_known_information(entity_name=ent_fact.entity_name, entity_label=label, facts=ent_fact.facts)
        return Entity(entity_name=ent_fact.entity_name, facts=ent_fact.facts, entity_label=label, summary=entity_summary)


if __name__ == "__main__":
    youbot_user = get_youbot_user_by_id(1)
    archival_messages = get_archival_messages(youbot_user)

    entities = []
    for ent_fact in tqdm(calculate_ents_facts(youbot_user, archival_messages)):
        entity = calculate_entity(ent_fact)
        if entity:
            upsert_memory_entity(
                youbot_user=ent_fact.youbot_user, entity_name=entity.entity_name, entity_label=entity.entity_label.name, text=entity.summary
            )
            entities.append(entity)

    # pickle results
    with open("entities.pkl", "wb") as f:
        pickle.dump(entities, f)
