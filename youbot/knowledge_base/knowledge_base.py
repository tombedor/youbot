from dataclasses import dataclass
import logging
import pickle
from typing import Generator, List, Set
import pandas as pd
from pandas import DataFrame
import spacy
from spacy.tokens.doc import Doc
from tqdm import tqdm
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


ENTITY_LABEL_CONFIDENCE_THRESHOLD = 0.7


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
class PrecursorEntFacts:
    entity_name: str
    facts: Set[str]
    initial_labels: Set[str]


def get_ents_facts(archival_messages: List[ArchivalMemoryModel]) -> Generator[PrecursorEntFacts, None, None]:
    names_to_facts = {}
    names_to_labels = {}
    
    for archival_msg in tqdm(archival_messages, "processing messages"):
        enriched_doc = NLP.process(archival_msg.text)  # type: ignore
        for ent in enriched_doc.ents:
            names_to_facts.setdefault(ent.text, set()).add(archival_msg.text)
            names_to_labels.setdefault(ent.text, set()).add(ent.label_)
    for name in names_to_facts.keys():
        yield PrecursorEntFacts(entity_name=name, facts=names_to_facts[name], initial_labels=names_to_labels[name])
        
@dataclass
class FactEntities:
    fact: str
    entities: List[Entity]
        

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
        if ent_label in EntityLabel.__members__:
            return EntityLabel[winning_label] # type: ignore
        else:
            raise KeyError(f"Invalid label: {winning_label}")


def summarize_known_information(entity_name: str, entity_label: EntityLabel, facts: Set[str]) -> str:
    raw_facts_list = list(facts)
    raw_facts_list.sort()
    facts_list = [f"Entity name: {entity_name}. Entity Label: {entity_label.name}"]
    summary_prompt = entity_label.summary_prompt
    
    
    response = query_llm(prompt = "\n".join(facts_list), system= summary_prompt)
    assert response
    return response

def get_entity(name: str, facts: Set[str], label: EntityLabel) -> Entity:
    summary = summarize_known_information(entity_name=name, entity_label=label, facts=facts)
    return Entity(entity_name=name, entity_label=label, facts=facts, summary=summary)
    

def run(youbot_user: YoubotUser, persist: bool = True) -> None
    archival_messages = get_archival_messages(youbot_user)
    
    facts_to_entities = {}
    entities = []
    for ent_facts in get_ents_facts(archival_messages):
        label = calculate_label_for_entity_name(ent_facts)
        entity_summary = summarize_known_information(entity_name=ent_facts.entity_name, entity_label=label, facts=ent_facts.facts)
        entity = Entity(entity_name=ent_facts.entity_name, facts=ent_facts.facts, entity_label=label, summary=entity_summary)
        if persist:
            upsert_memory_entity(youbot_user = youbot_user, entity_name=entity.entity_name, entity_label=entity.entity_label.name, text=entity.summary)
        for fact in entity.facts:
            facts_to_entities.setdefault(fact, []).append(entity)
            entities.append(entity)
            
    for fact, entities in facts_to_entities.items():
        # do relationship resolution
        ...
        
        
        

        # filename = os.path.join(CACHE_DIR, "knowledge_base_entities.pkl")
        # with open(filename, "wb") as f:
        # pickle.dump(entities, f)

        # for entity in entities:
        # logging.info("Processed entity %s", entity.entity_name)
        # self.kb.add_entity(entity=entity.entity_name, freq=len(entity.facts), entity_vector=get_embedding(entity.description()))

        # self.kb.to_disk(self.kb_filename)

    def process_relationships(self, final_entity_labels, initial_entity_labels_df) -> DataFrame:
        # pkl_path = os.path.join(self.cache_dir, "final_entity_relationships.pkl")
        # if os.path.exists(pkl_path):
        # return pd.read_pickle(pkl_path)

        ### Ask LLM for relationship labels
        # group entities by fact
        facts_with_entities = initial_entity_labels_df.groupby("fact")["name"].apply(lambda x: set(x)).reset_index()
        relation_rows = []
        for _, row in tqdm(facts_with_entities.iterrows()):
            fact = row["fact"]
            entities = row["name"]

            if len(entities) < 2:
                continue

            for entity_1 in entities:
                for entity_2 in entities:
                    if entity_1 == entity_2:
                        continue
                    label_1 = final_entity_labels[final_entity_labels["name"] == entity_1]["label"].values[0]
                    label_2 = final_entity_labels[final_entity_labels["name"] == entity_2]["label"].values[0]

                    score_1 = final_entity_labels[final_entity_labels["name"] == entity_1]["confidence_score"].values[0]
                    score_2 = final_entity_labels[final_entity_labels["name"] == entity_2]["confidence_score"].values[0]

                    if score_1 < ENTITY_LABEL_CONFIDENCE_THRESHOLD or score_2 < ENTITY_LABEL_CONFIDENCE_THRESHOLD:
                        continue

                    relationship_choices = VALID_RELATIONSHIPS.get((label_1, label_2), [])
                    if len(relationship_choices) == 0:
                        continue

                    prompt = f"""You are an entity resolution assistant. 
                    You must classify the relationship between two entities:
                    Entity 1: name = {entity_1}, type = {label_1} 
                    Entity 2: name = {entity_2}, type = {label_2}
                
                    The valid choices are: {relationship_choices}. If none fit specify NONE.
                    
                    Use both your inherent knowledge, and this fact derived from chat logs:
                    {fact}
                    
                    Your response begin with one of the following choices: {relationship_choices}, NONE. 
                    A score from 1 to 100 should follow. 100 means you are very confident in your choice, 1 means you are not confident at all.
                    Then it should follow with a short explanation of your reasoning.
                    """

                    response = query_llm(prompt)
                    assert response

                    # winning_label, score = self.get_winner_and_score(response, relationship_choices)
                    # row = {
                    #     "entity_1": entity_1,
                    #     "entity_2": entity_2,
                    #     "relationship": winning_label,
                    #     "score": score,
                    #     "fact": fact,
                    #     "llm_respnose": response,
                    # }
                    # relation_rows.append(row)

        llm_relation_df = pd.DataFrame(relation_rows)

        ### pick winners
        min_score = llm_relation_df["score"].min() - 1
        max_score = llm_relation_df["score"].max()
        llm_relation_df["score"] = (llm_relation_df["score"] - min_score) / (max_score - min_score)

        entity_and_relationship_totals = (
            llm_relation_df.groupby(["entity_1", "entity_2", "relationship"]).agg({"score": "sum"}).reset_index()
        )

        entity_and_relationship_totals["confidence_score"] = entity_and_relationship_totals["score"]

        entity_and_relationship_totals["total_scores_for_entity_pair"] = entity_and_relationship_totals.groupby(["entity_1", "entity_2"])[
            "score"
        ].transform("sum")

        entity_and_relationship_totals["confidence_score"] = (
            entity_and_relationship_totals["score"] / entity_and_relationship_totals["total_scores_for_entity_pair"]
        )

        final_entity_relationships = (
            entity_and_relationship_totals.sort_values("confidence_score", ascending=False)
            .drop_duplicates(["entity_1", "entity_2"])
            .reset_index()
        )

        # with open(os.path.join(self.cache_dir, "final_entity_relationships.pkl"), "wb") as f:
        # pd.to_pickle(final_entity_relationships, f)

        return final_entity_labels

    # def create_knowledge_base_enties(self):
    #     entities = []
    #     for entity_label_data in self.get_entity_label_data():
    #         if entity_label_data.label == EntityLabel.PERSON:
    #             entity = Person(entity_name=entity_label_data.name)
    #         elif entity_label_data.label == EntityLabel.PET:
    #             entity = Pet(entity_name=entity_label_data.name)
    #         elif entity_label_data.label == EntityLabel.PRIMARY_USER:
    #             entity = PrimaryUser(entity_name=entity_label_data.name)
    #         else:
    #             logging.info("Skipping entity %s with label %s", entity_label_data.name, entity_label_data.label)
    #             continue

    #         logging.info("Processing entity %s", entity_label_data.name)
    #         for fact in entity_label_data.facts:
    #             entity.query_llm_for_attrs(fact)
    #         entities.append(entity)

    #     filename = os.path.join(self.cache_dir, "knowledge_base_entities.pkl")

    #     with open(filename, "wb") as f:
    #         pickle.dump(entities, f)

    #     return entities


if __name__ == "__main__":
    youbot_user = get_youbot_user_by_id(1)
    entities = run(youbot_user)

    # pickle results
    with open("entities.pkl", "wb") as f:
        pickle.dump(entities, f)
