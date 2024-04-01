from bertopic import BERTopic

# import spacy.kb.

topic_model = BERTopic("english")
<<<<<<< HEAD
with open("/tmp/archival.txt") as f:
    docs = [f.read()]

||||||| parent of 6d4f3d7 (kb)
with open('/tmp/archival.txt') as f:
    docs = [f.read()]
    
=======
with open('/tmp/archival.txt') as f:
    docs = f.readlines()
    
>>>>>>> 6d4f3d7 (kb)
topics, probs = topic_model.fit_transform(docs)
print(topics, probs)

<<<<<<< HEAD
topic_model.get_topics(True)
||||||| parent of 6d4f3d7 (kb)
topic_model.get_topics(True)
=======
print(topic_model.get_topics(True))


import spacy
from transformers import BertModel, BertTokenizer
import torch

# Initialize the tokenizer and model
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')

# Initialize the language model
nlp = spacy.blank('en')

# Initialize the Knowledge base
kb = nlp.create_kb()

# Sentence or description representing the entity
sentence = 'Justina is engaged to Tom.'

# Tokenize the sentence and return torch tensors
inputs = tokenizer(sentence, return_tensors='pt')

# Run the sentence through the model
outputs = model(**inputs)

# Fetch the embeddings of the [CLS] token
entity_vector = outputs.last_hidden_state[0][0]

# Now you can add this entity_vector to your knowledge base
# 'Q1' is a placeholder for the entity ID
kb.add_entity(entity='Q1', entity_vector=entity_vector.detach().numpy(), freq=34)
>>>>>>> 6d4f3d7 (kb)
