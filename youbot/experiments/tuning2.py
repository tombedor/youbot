import spacy

nlp = spacy.load('en_core_web_sm') # Loads the English model

chat_messages = ["Hey, John! Do you want to catch a movie tonight at Regal Cinema?"]
labels = []

for message in chat_messages:
    doc = nlp(message)
    entities = [(ent.label_, ent.start_char, ent.end_char) for ent in doc.ents]
    
    label = ['O'] * len(message)
    for entity in entities:
        label_type = 'B-' + entity[0]
        start = entity[1]
        end = entity[2]
        
        label[start] = label_type
        for i in range(start+1, end):
            label[i] = 'I-' + entity[0]
    
    labels.append(' '.join(label))

print(labels)