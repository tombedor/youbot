# https://medium.com/mantisnlp/constructing-a-knowledge-base-with-spacy-and-spacy-llm-f65b50ea53d
# https://spacy.io/api/large-language-models#rel-v1

import os
from re import L
from time import sleep
from spacy_llm.util import assemble
import spacy


dir_path = os.path.dirname(os.path.realpath(__file__))

config = os.path.join(dir_path, "config.cfg")

model_name = 'en_core_web_md'
try:
    nlp = assemble(config)
except OSError:
    spacy.cli.download(model_name)
    nlp = assemble(config)

from datasets import load_dataset
print('downloading data')
docs = [d['text'] for d in load_dataset("argilla/news-summary")['train']][0:10] # type: ignore
total = len(docs)

docs_with_rels = []
i = 0
for doc in docs:
    print("processing", i, "of", total)
    try:
        new_doc = nlp(doc)
        docs_with_rels.append(new_doc)
        i +=1 
    except Exception as e:
        print(f'failed: {e}')
        sleep(5)
        
print('finished with docs')
relation_data = []
total = len(docs_with_rels)
i = 0
for doc in docs_with_rels:
    print("processing", i, "of", total)
    for rel in doc._.rel:
        dep, relation, dest = doc.ents[rel.dep], rel.relation, doc.ents[rel.dest]
        relation_data.append([dep, relation, dest])
    i += 1

from pyvis.network import Network
net = Network('500px', '500px', notebook=True, cdn_resources='in_line')

nodes = []
for r in relation_data:
    if r[0] not in nodes:
        nodes.append(r[0])
    if r[2] not in nodes:
        nodes.append(r[2])
net.add_nodes(nodes)
for r in relation_data:
    net.add_edge(r[0], r[2], value=1, title=r[1])

net.show('nx.html')
    