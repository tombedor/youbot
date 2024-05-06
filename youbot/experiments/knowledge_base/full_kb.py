# full kb: https://spacy.io/api/kb#get_candidates

# vectors are calculated via descriptions of the model

from datetime import timedelta
import os
from spacy.kb import InMemoryLookupKB
from youbot.store import Store


from spacy.lang.en import English

# 0. Create documents as transcription logs of converstaions
messages = Store().get_memgpt_recall()

# batch messages into conversations. If pause is greater than MAX_CONVO_PAUSE, start a new conversation.
# some messages have null timestamp. in this case, use the last non-null timestamp.
conversation_message_collections = []
MAX_CONVO_PAUSE = timedelta(minutes=60)

current_convo_messages = []
for msg in messages:
    if msg.role != "user":
        continue
    # check if we need to rest the convo
    if len(current_convo_messages) > 0 and msg.time - current_convo_messages[-1].time > MAX_CONVO_PAUSE:
        conversation_message_collections.append(current_convo_messages)
        current_convo_messages = []
    current_convo_messages.append(msg)
    last_message_time = msg.time


conversations = []
for convo_messages in conversation_message_collections:
    convo_text = ""
    for msg in convo_messages:
        convo_text += msg.content + "\n"
    conversations.append(convo_text)


print("foo")

tmpdir = "/tmp/convo_test"

# do i maybe want to only have user messages?

os.makedirs(tmpdir, exist_ok=True)
for idx, convo in enumerate(conversations):
    with open(os.path.join(tmpdir, f"convo_{idx}.txt"), "w") as f:
        f.write(convo)


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
