# from bertopic import BERTopic

# # import spacy.kb.

# topic_model = BERTopic("english")
# with open("/tmp/archival.txt") as f:
#     docs = f.readlines()

# topics, probs = topic_model.fit_transform(docs)
# print(topics, probs)

# print(topic_model.get_topics(True))


# import spacy
# from transformers import BertModel, BertTokenizer

# # Initialize the tokenizer and model
# tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
# model = BertModel.from_pretrained("bert-base-uncased")

# # Initialize the language model
# nlp = spacy.blank("en")

# # Initialize the Knowledge base
# kb = nlp.create_kb()

# # Sentence or description representing the entity
# sentence = "Justina is engaged to Tom."

# # Tokenize the sentence and return torch tensors
# inputs = tokenizer(sentence, return_tensors="pt")

# # Run the sentence through the model
# outputs = model(**inputs)

# # Fetch the embeddings of the [CLS] token
# entity_vector = outputs.last_hidden_state[0][0]

# # Now you can add this entity_vector to your knowledge base
# # 'Q1' is a placeholder for the entity ID
# kb.add_entity(entity="Q1", entity_vector=entity_vector.detach().numpy(), freq=34)
