# full kb: https://spacy.io/api/kb#get_candidates

# vectors are calculated via descriptions of the model

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
if os.path.exists('/tmp/checkpoint.pkl'):
    with open('/tmp/checkpoint.pkl', 'rb') as f:
        docs_with_entities = pickle.load(f)
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

    docs_with_entities = [nlp(doc) for doc in tqdm(docs)]

    with open('/tmp/checkpoint.pkl', 'wb') as f:
        pickle.dump(docs_with_entities, f)
        
        
@dataclass
class KbEntity:
    name: str
    label: str
    facts: Set[str]
    
    def id(self) -> Tuple[str, str]:
        return (self.name, self.label)    
    
if os.path.exists('/tmp/checkpoint2.pkl'):
    kb_entities = pickle.load(open('/tmp/checkpoint2.pkl', 'rb'))
else:
    kb_entities = {}

    for doc in docs_with_entities:
        for ent in doc.ents:
            if (ent.text, ent.label_) not in kb_entities:
                kb_entities[(ent.text, ent.label_)] = KbEntity(ent.text, ent.label_, set())
            kb_entities[(ent.text, ent.label_)].facts.add(doc.text)
        
    with open('/tmp/checkpoint2.pkl', 'wb') as f:
        pickle.dump(kb_entities, f)        
    

from transformers import T5ForConditionalGeneration, T5Tokenizer
model = T5ForConditionalGeneration.from_pretrained('t5-base')
tokenizer = T5Tokenizer.from_pretrained('t5-base')


Doc.set_extension('summary', default=None)
Doc.set_extension('entity_label', default=None)
Doc.set_extension('entity_name', default=None)

def summarize_text(text):
    inputs = tokenizer.encode('summarize: ' + text, return_tensors='pt', max_length=512, truncation=True)
    outputs = model.generate(inputs, max_length=150, min_length=40, length_penalty=2.0, num_beams=4, early_stopping=True)
    return tokenizer.decode(outputs[0])

def summarization_component(doc):
    doc._.summary = summarize_text(doc.text)
    return doc

    

summarize_nlp = spacy.load('en_core_web_md')
summarize_nlp.add_pipe(summarization_component, last=True)


final_docs = []
for kb in tqdm(kb_entities.values()):
    words = sum([f.split() for f in kb.facts], [])
    doc = Doc(summarize_nlp.vocab, words=words)
    doc._.entity_name = kb.name
    doc._.entity_label = kb.label
    final_doc = summarize_nlp(doc)


with open('/tmp/checkpoint3.pkl', 'wb') as f:
    pickle.dump(final_docs, f)
print('foo')
    
