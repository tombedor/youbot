import logging
import os
import outlines.models.transformers
import spacy
from spacy.kb import InMemoryLookupKB
import spacy.kb.kb_in_memory
import spacy.cli

from youbot import STORAGE_DIR, log_to_stdout
from youbot.experiments.q_and_a_dataset_generation import retrieve_archival_memories
import outlines.models

outlines.models.transformers

log_to_stdout()

model_name = "en_core_web_lg"
kb_path = os.path.join(STORAGE_DIR, "knowledge_base")

try:
    nlp = spacy.load(model_name)
except OSError:
    spacy.cli.download(model_name)
    nlp = spacy.load(model_name)


# the `vocab` argument should be a `Vocab` instance which is shared with other pipeline components
kb = InMemoryLookupKB(vocab=nlp.vocab, entity_vector_length=300)
try:
    kb.from_disk(kb_path)
except ValueError:
    logging.info("assuming kb has not yet been written to disk")


dialog_fragments = retrieve_archival_memories()
entities_freq = {}

for dialog_fragment in dialog_fragments:
    doc = nlp(dialog_fragment)
    for ent in doc.ents:
        logging.info(f"entity: {ent.text}")
        if ent.text not in entities_freq:
            entities_freq[ent.text] = {"vector": nlp(ent.text).vector, "frequency": 1}
        else:
            entities_freq[ent.text]["frequency"] += 1

for entity, info in entities_freq.items():
    kb.add_entity(entity, info["frequency"], info["vector"])


all_entity_ids = kb.get_entity_strings()

for entity_id in all_entity_ids:
    # Print entity ID
    print(f"Entity ID: {entity_id}")

    # Get and print entity vector
    entity_vector = kb.get_vector(entity_id)
    print(f"Entity Vector: {entity_vector}")

    # Get and print aliases for the entity
    # aliases = kb.get(entity_id)
    # for alias in aliases:
    # print(f"Alias: {alias['alias']}, Prior Probability: {alias['prob']}")


# # Save the knowledge base to disk
kb.to_disk(kb_path)


# https://spacy.io/universe/project/bertopic
