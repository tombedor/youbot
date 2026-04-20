# ADR 003: Youbot-Owned Adapters

## Status

Accepted

## Context

The initial design required each child repo to provide repo-local Textual integration code. That approach tightly couples child repos to a specific UI framework and forces them to carry presentation concerns that belong to the orchestrator.

## Decision

Youbot will own repo adapters and any Textual-specific rendering code.

Adapters will live in youbot-controlled local storage and may contain:

- discovered commands
- parsing and rendering hints
- command-palette entries
- structured view definitions

Integrated repos are not required to ship Textual code or repo-local plugins.

## Consequences

Positive:
- Child repos stay decoupled from Textual
- UI concerns remain inside the orchestrator
- Adapter behavior can evolve without changing child repos

Negative:
- Youbot must maintain more local state
- Rich views depend on good command output conventions or adapter heuristics

## Rejected alternatives

### Require `youbot_plugin.py` in each repo

Rejected because it locks child repos into Textual and inverts the dependency boundary.

### Use only plain text command output with no adapter layer

Rejected because it would make structured views and repo-specific UI behavior much harder to implement cleanly.
