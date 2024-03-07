from bertopic import BERTopic

topic_model = BERTopic("english")
with open('/tmp/archival.txt') as f:
    docs = [f.read()]
    
    
    



topics, probs = topic_model.fit_transform(docs)
print(topics, probs)

topic_model.get_topics(True)