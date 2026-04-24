# ADR 007: Tmux-Managed Coding-Agent Sessions

## Status

Accepted

## Context

Youbot needs to support long-lived coding work across multiple repos without pretending that its own chat transcript is the primary control surface for that work.

The previous continuation model emphasized backend-native non-interactive resume commands. That approach preserved backend semantics better than transcript reconstruction, but it still treated coding work as something youbot launched and summarized rather than a real terminal session the user could attach to.

The concrete product requirement is stronger:

- start or resume coding-agent sessions
- track those sessions as explicit tasks
- let the user attach to the real session through `tmux`
- avoid building a message-interception layer that tries to proxy the coding agent conversation

## Decision

Youbot will manage coding-agent work through named `tmux` sessions.

For each repo coding workspace, youbot stores:

- backend name
- `tmux` session metadata
- linked task id when work is active
- optional backend-native continuation handle if the backend exposes one
- short purpose or summary
- status and timestamps

When a code-change task starts or resumes, youbot launches or reuses the repo's managed `tmux` session and starts the selected backend inside that terminal workspace.

Youbot may tail recent terminal output into its UI for observability, but the `tmux` session is the source of truth for active coding work. The user-facing action is attachment to that session, not transcript interception.

Backend-native session ids remain useful as optional metadata for backends that support native continuation, but they are secondary to the `tmux` workspace handle in youbot's orchestration model.

## Consequences

Positive:
- The user can inspect or take over real agent sessions directly
- Long-lived coding work survives TUI restarts more naturally
- Youbot's task model can point at concrete terminal workspaces
- The system avoids becoming a fragile proxy chat layer for coding agents

Negative:
- `tmux` becomes a required runtime dependency for coding-session management
- The runner must handle `tmux` lifecycle, naming, discovery, and stale-session cleanup
- Some backend-specific continuation flows may need adaptation to fit inside the managed workspace model

## Rejected alternatives

### Proxy the coding-agent conversation through youbot

Rejected because it would make youbot responsible for relaying and interpreting every message in a workflow that already has a native terminal interaction model.

### Treat backend-native non-interactive continuation as the only session model

Rejected because it does not satisfy the requirement that the user should be able to attach to the real ongoing session and work in it directly.
