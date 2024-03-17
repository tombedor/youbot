import spacy
# import en_core_web_sm
# Load the pre-trained model
with open('/tmp/recall.txt', 'r') as f:
    text = f.read()
    
nlp = spacy.load('en_core_web_sm')

# Process a text
doc = nlp(text)

# Iterate over the entities
for ent in doc.ents:
    print(ent.text, ent.label_)