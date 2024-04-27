# full kb: https://spacy.io/api/kb#get_candidates
# also: https://spacy.io/usage/large-language-models
# vectors are calculated via descriptions of the model


####################
# Store entities, resolve which facts are relevant to which entities, summarize
# result: summaries aren't all that useful, there's a hot key issue. 

import os
import pickle
from typing import Set, Tuple
from attr import dataclass
from tqdm import tqdm
from youbot.store import Store
from spacy.tokens import Doc





# 0. Create documents as transcription logs of converstaions
docs = Store().get_archival_messages()


import os
from spacy_llm.util import assemble
import spacy

# if checkpoint file exists, load it
if os.path.exists('/tmp/3checkpoint.pkl'):
    with open('/tmp/checkpoint.pkl', 'rb') as f:
        docs_with_rels = pickle.load(f)
else:
    dir_path = os.path.dirname(os.path.realpath(__file__))

    config = os.path.join(dir_path, "config.cfg")

    model_name = 'en_core_web_md'
    try:
        nlp = assemble(config)
    except OSError:
        spacy.cli.download(model_name)
        nlp = assemble(config)

    total = len(docs)

    docs_with_rels = [nlp(doc) for doc in tqdm(docs)]

    with open('/tmp/3checkpoint.pkl', 'wb') as f:
        pickle.dump(docs_with_rels, f)
        
        
@dataclass
class KbEntity:
    name: str
    label: str
    facts: Set[str]
    
    def id(self) -> Tuple[str, str]:
        return (self.name, self.label)    
    
if os.path.exists('/tmp/3checkpoint2.pkl'):
    kb_entities = pickle.load(open('/tmp/3checkpoint2.pkl', 'rb'))
else:
    kb_entities = {}

    for doc in docs_with_rels:
        for ent in doc.ents:
            if (ent.text, ent.label_) not in kb_entities:
                kb_entities[(ent.text, ent.label_)] = KbEntity(ent.text, ent.label_, set())
            kb_entities[(ent.text, ent.label_)].facts.add(doc.text)
        
    with open('/tmp/3checkpoint2.pkl', 'wb') as f:
        pickle.dump(kb_entities, f)       

Doc.set_extension('summary', default=None)
Doc.set_extension('entity_label', default=None)
Doc.set_extension('entity_name', default=None)

summarize_nlp = spacy.load('en_core_web_md')
# for more options on llm see https://spacy.io/api/large-language-models#config
summarize_nlp.add_pipe('llm_summarization', last=True)


final_docs = []

for kb in tqdm(kb_entities.values()):
    if len(kb.facts) == 1:
        final_docs.append(summarize_nlp(kb.facts.pop()))
        continue
    else:
        words = sum([f.split() for f in kb.facts], [])
        doc = Doc(summarize_nlp.vocab, words=words)
        doc._.entity_name = kb.name
        doc._.entity_label = kb.label
        final_docs.append(summarize_nlp(doc))


# summaries are maybe not useful. we might instead need to just vectorize all the facts and use relations between them

with open('/tmp/checkpoint3.pkl', 'wb') as f:
    pickle.dump(final_docs, f)

    
# add relational data, and if two entities are in a conversation, add the relation
    
