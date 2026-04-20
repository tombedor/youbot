# ADR 001: Session Model

## Status

Accepted

## Context

Youbot is a conversational orchestrator spanning multiple repos. A single flat conversation history would mix unrelated contexts together and degrade routing quality over time. The product requirement is to resume work naturally when returning to a repo while still supporting cross-repo requests.

## Decision

Youbot will persist sessions in two scopes:

- one global session for orchestrator-level and cross-repo interactions
- one per-repo session for repo-specific work

When a user returns to a repo, youbot resumes that repo's current session by default.

## Consequences

Positive:
- Repo-specific context remains focused
- Routing quality improves because the relevant history is narrower
- Restart behavior is intuitive

Negative:
- Session storage is more complex than a single transcript
- Cross-repo context may need deliberate promotion into the global session

## Rejected alternatives

### Single global conversation

Rejected because it causes context pollution and makes repo switching ambiguous.

### One session per tab or view only

Rejected because it ties persistence to UI state rather than product semantics.
