# Interfaces

## Purpose

This document defines the canonical internal records and service interfaces for youbot. A coding agent should use these interfaces to avoid drifting into incompatible ad hoc structures.

## Canonical records

These records may be implemented as dataclasses, Pydantic models, typed dicts, or similar typed structures. The important requirement is that the field meanings remain stable.

### `RepoRecord`

Represents one registered repo.

Required fields:

```python
repo_id: str
name: str
path: str
classification: Literal["integrated", "managed"]
status: Literal["ready", "invalid", "missing", "error"]
```

Optional fields:

```python
purpose_summary: str | None
tags: list[str]
preferred_commands: list[str]
last_scanned_at: str | None
last_active_at: str | None
adapter_id: str | None
```

Invariants:
- `repo_id` is stable across restarts
- `path` points to the repo root
- `classification` drives policy, not capability

### `CommandRecord`

Represents one discovered `just` recipe.

```python
repo_id: str
command_name: str
display_name: str
description: str | None
invocation: list[str]
supports_structured_output: bool
structured_output_format: Literal["json", "text", "unknown"]
tags: list[str]
```

Invariants:
- `invocation` is executable from the repo root
- `command_name` is unique within a repo

### `SessionMessage`

Represents one item in a conversation history.

```python
message_id: str
scope: Literal["global", "repo"]
repo_id: str | None
role: Literal["user", "assistant", "system", "tool"]
content: str
created_at: str
```

Invariants:
- `repo_id` is set when `scope == "repo"`
- global messages must have `repo_id is None`

### `SessionRecord`

Represents one persisted conversation thread.

```python
session_id: str
scope: Literal["global", "repo"]
repo_id: str | None
messages: list[SessionMessage]
updated_at: str
```

### `RouteDecision`

The router's structured output.

```python
repo_id: str | None
action_type: Literal["command", "query", "code_change", "clarify", "global_action"]
command_name: str | None
arguments: list[str]
reasoning_summary: str
confidence: float
```

Invariants:
- `command_name` is required when `action_type == "command"`
- `repo_id` may be `None` only for global actions or clarifications
- `confidence` is normalized to `0.0 <= x <= 1.0`

### `ExecutionResult`

Represents a completed command execution.

```python
repo_id: str
command_name: str
invocation: list[str]
exit_code: int
stdout: str
stderr: str
started_at: str
finished_at: str
duration_ms: int
parsed_payload: dict | list | None
```

### `AdapterRecord`

Represents a youbot-owned adapter for a repo.

```python
adapter_id: str
repo_id: str
version: str
view_names: list[str]
command_palette_entries: list[str]
output_rules: list[str]
updated_at: str
```

## Service interfaces

These are logical interfaces. Implementations may vary, but the contracts should remain intact.

### `Registry`

Responsibilities:
- CRUD for repo metadata
- Store and retrieve command inventory
- Store routing hints and adapter references

Suggested methods:

```python
register_repo(path: str, name: str | None = None) -> RepoRecord
get_repo(repo_id: str) -> RepoRecord
list_repos() -> list[RepoRecord]
update_repo(repo: RepoRecord) -> RepoRecord
store_commands(repo_id: str, commands: list[CommandRecord]) -> None
list_commands(repo_id: str) -> list[CommandRecord]
```

### `SessionStore`

Responsibilities:
- Persist global and per-repo sessions
- Append messages
- Load scoped histories for routing

Suggested methods:

```python
get_global_session() -> SessionRecord
get_repo_session(repo_id: str) -> SessionRecord
append_message(message: SessionMessage) -> None
reset_session(scope: str, repo_id: str | None = None) -> None
```

### `JustfileParser`

Responsibilities:
- Read a `justfile`
- Extract recipes into canonical `CommandRecord` values

Suggested methods:

```python
parse_repo(repo: RepoRecord) -> list[CommandRecord]
```

### `Router`

Responsibilities:
- Produce a `RouteDecision` from message + context

Suggested methods:

```python
route(
    user_message: str,
    active_repo_id: str | None,
    global_session: SessionRecord,
    repo_session: SessionRecord | None,
    repos: list[RepoRecord],
    commands: dict[str, list[CommandRecord]],
) -> RouteDecision
```

### `Executor`

Responsibilities:
- Execute a discovered command and normalize the result

Suggested methods:

```python
run(repo: RepoRecord, command: CommandRecord, arguments: list[str]) -> ExecutionResult
```

### `AgentSpawner`

Responsibilities:
- Invoke `claude` for code-change requests

Suggested methods:

```python
run_code_change(repo: RepoRecord, request: str, context: str | None = None) -> str
```

### `AdapterLoader`

Responsibilities:
- Load local adapter definitions for a repo
- Provide palette entries and output rendering rules

Suggested methods:

```python
load(repo_id: str) -> AdapterRecord | None
save(adapter: AdapterRecord) -> None
refresh(repo: RepoRecord, commands: list[CommandRecord]) -> AdapterRecord
```

## Ownership rules

- The registry owns repo and command metadata.
- The session store owns conversation history.
- The adapter loader owns adapter definitions and rendering hints.
- The executor owns subprocess execution details.
- The TUI owns presentation, not domain decisions.
- The router owns repo/action selection.

## Serialization rules

- Persist timestamps in ISO 8601 UTC format.
- Persist stable ids rather than deriving ids from list position.
- Avoid storing derived display text when the source record is sufficient.
- Structured command payloads should be stored separately from raw stdout when possible.

## Deferrable decisions

These do not need to be fixed before implementation starts:

- JSON files versus SQLite for persistence
- Dataclasses versus Pydantic models
- Exact Textual screen and widget breakdown
- How rich adapter definitions should be in v1
