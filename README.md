# YouBot

An AI personal assistant with long term memory.

## Roadmap

### Clients
- [x] command line client
- [x] Discord client
- [ ] SMS client
- [ ] WhatsApp client
- [ ] Discord voice client

### User onboarding
- [ ] Signup page
- [ ] Onboarding flow
- [ ] Updated onboarding, smooth initial conversation to capture initial information about user. Agent should take more initiative in learning about the user, without being spammy

### Integrations
- [x] [MemGPT](https://memgpt.ai)
- [ ] [Zep](https://github.com/getzep/zep)

### Toolsets
- [ ] Google calendar
- [ ] Generic reminders
- [ ] RSS / feed summarizing
- [ ] Command line refinement (consume from stderr?)

## Experiments
General goals: Smooth, immersive, personalized conversation. Minimal capabilities.

### "Personal wikipedia": Form reference document from chat history
Idea: create pipeline that re-processes chat logs, iteratively building a mini-Wikipedia.

The agent struggled to form coherent articles. Irrelevant and repeated information kept being included. 

### "Delegates": Allow agents to spawn other agents
Idea: Allow primary agent to delegate tasks to "helper agents". This could prevent the issue of large function sets cluttering the context window.

This was functional but high overhead, and slow. 

### Topic / entity resolution
Develop a "helper model" which intercepts chat messages and appends context.

Narrowly scoped, open source models

- BERT
- fine tuning with [axolotl](https://github.com/OpenAccess-AI-Collective/axolotl)


### Knowledge graph
- Persistence / management via [spacy](https://github.com/explosion/spaCy)

### Alternative LLMs
Open router?

Gemini: How does the larger context window impact what is needed from memory consolidation?

Suspicion: larger context window does not eliminate need for structured knowledge representation. If human "context window" is much smaller than the models, does the model become less relatable?

### Interesting resources
[Simon Willison](https://simonwillison.net/)
[Cererbal Valley](https://cerebralvalley.ai/blog)