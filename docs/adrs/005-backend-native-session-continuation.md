# ADR 005: Backend-Native Session Continuation

## Status

Superseded by ADR 007

## Context

Youbot needs to continue coding-agent work across invocations in repos such as `job_search`, `life_admin`, and `trader-bot`. A naive design would store transcripts inside youbot and attempt to reconstruct agent state on each code-change request.

That would duplicate the coding agent's own session model and create a fragile approximation of backend behavior.

## Decision

This ADR is superseded by [ADR 007](./007-tmux-managed-coding-agent-sessions.md).

The original decision to rely primarily on backend-native non-interactive continuation was replaced once the product direction shifted toward explicit session orchestration with `tmux` attachment. Backend-native continuation handles remain useful metadata, but they are no longer the primary session anchor in the architecture.

## Consequences

Positive:
- Youbot stays aligned with the backend's real session semantics
- Session continuation is simpler and less error-prone
- Youbot avoids becoming a second transcript manager for code agents
- Orchestration remains scriptable and deterministic

Negative:
- Continuation behavior is constrained by what each backend actually supports
- Youbot must handle backend-specific continuation flags and session-id discovery

## Rejected alternatives

### Reconstruct coding-agent sessions from youbot-side transcripts

Rejected because it duplicates backend behavior poorly and creates drift between youbot's model and the agent's actual session state.

### Treat each code-change request as a fresh agent invocation

Rejected because it loses valuable working context and makes ongoing repo work less effective.
