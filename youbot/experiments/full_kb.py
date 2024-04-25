# full kb: https://spacy.io/api/kb#get_candidates

# vectors are calculated via descriptions of the model

from spacy.kb import InMemoryLookupKB
from youbot.store import Store


from spacy.lang.en import English

# 0. Create documents as transcription logs of converstaions
messages = Store().get_memgpt_recall()

print('foo')



nlp = English()
vocab = nlp.vocab
kb = InMemoryLookupKB(vocab=vocab, entity_vector_length=64)

# pipeline: 
#### naive knowledge base ####
# 1. ner from text using en_core_web_md
# 2. for each entity, extract a fact about the entity, and save the text.
# 3. use BERT or Word2Vect to get the vector for the entity.
# 4. save all entities to the knowledge base.
#### de-duplicate and de-conflate
# 5. For each set of facts, evaluate if the text seems to describe one entity, or multiple.
# 6, For each entity in the knowledge base, search the alias and evaluate if the different sets of facts actually describe one entity.
# 7. If the facts describe one entity, merge the entities.
#### capture uncertainty of matches
# 8. Set thresholds for querying the knowledge base. If multiple entities match well with context, or if matches produce a low score, prompt the chat agent to explicitly ask for clarification. Capture this output in a set of validated facts
