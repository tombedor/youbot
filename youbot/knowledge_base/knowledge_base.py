import logging
import os
import pandas as pd
from pandas import DataFrame
import spacy
from tqdm import tqdm
from youbot.data_models import YoubotUser
from youbot.clients.llm_client import query_llm
from youbot.knowledge_base.entity import (
    EntityLabel,
    Person,
    Pet,
    PrimaryUser,
    calculate_label_for_entity_name,
)
from youbot.store import get_archival_messages, get_youbot_user_by_id, upsert_memory_entity

MODELS = ["gpt-3.5-turbo-0125", "gpt-3.5-turbo-instruct", "gpt-4o"]

NLP = spacy.load("en_core_web_md")


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


NLP = spacy.load("en_core_web_md")


class KnowledgeBase:
    def __init__(self, youbot_user: YoubotUser):
        self.youbot_user = youbot_user

    def process_entities(self) -> None:
        entity_name_to_facts = {}
        entity_name_to_initial_label = {}
        for archival_msg in tqdm(get_archival_messages(), "processing messages"):
            enriched_doc = NLP(archival_msg.text)  # type: ignore
            for ent in enriched_doc.ents:
                entity_name_to_initial_label.setdefault(ent.text, set()).add(ent.label_)
                entity_name_to_facts.setdefault(ent.text, set()).add(archival_msg.text)

        entities = []
        for entity_name, facts in tqdm(entity_name_to_facts.items(), "determining entity labels"):
            if len(entity_name_to_initial_label[entity_name]) == 1:
                prior_label = list(entity_name_to_initial_label[entity_name])[0]
            else:
                prior_label = None

            facts_list = list(facts)
            facts_list.sort()
            entity_label = calculate_label_for_entity_name(entity_name, tuple(facts_list), prior_label)

            if entity_label == EntityLabel.PERSON.name:
                entity = Person(entity_name=entity_name, facts=facts)
                entities.append(entity)
            elif entity_label == EntityLabel.PET.name:
                entity = Pet(entity_name=entity_name, facts=facts)
                entities.append(entity)
            elif entity_label == EntityLabel.PRIMARY_USER.name:
                entity = PrimaryUser(entity_name=entity_name, facts=facts)
                entities.append(entity)
            else:
                logging.info("Skipping entity %s with label %s", entity_name, entity_label)
                continue

        for entity in tqdm(entities, "processing entities"):
            entity.determine_attributes()
            upsert_memory_entity(
                youbot_user_id=self.youbot_user.id,
                entity_name=entity.entity_name,
                entity_label=entity.entity_label.name,
                text=entity.description(),
            )
            logging.debug("Processed entity %s: %s", entity.entity_name, entity.__dict__)

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
    # direct logs to stdout
    kb = KnowledgeBase(youbot_user=get_youbot_user_by_id(1))
    kb.process_entities()
