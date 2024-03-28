# Personalizing a Q/A model

The overall goal is to enhance the conversational model such that conversation outputs reflect knowledge of an individual user

Two primary approaches:

## Fine tuning the conversational model
Here, the conversational model itself is fine tuned with discussion including knowledge of the user. Training data is synthetically generated:
1) Relevant facts are identified
2) A conversational model is asked to generate synthetic outputs for each relevant fact
3) The model is fine tuned

The drawback of this approach is that the model needs to be trained on a large amount of data.


I tried this with T5 model, using PEFT prefix tuning. The outputs thus far are not promising

## Auxilary NER model
Here, a separate NER model is used to identify entities in the conversation and then these are fed into the conversational model as auxiliary inputs.

The model itself seems easier to train, as the outputs should be more constrained.

An initial step for this could be generate conversational inputs using a predefined set of facts.

If this works, it could be extended such that a knowledge graph is maintained.