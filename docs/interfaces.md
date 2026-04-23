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

### `ConversationMessage`

Represents one item in youbot's own conversation history.

```python
message_id: str
role: Literal["user", "assistant", "system", "tool"]
content: str
created_at: str
```

Invariants:
- Messages belong to youbot's orchestration conversation, not to backend-native coding-agent transcripts

### `ConversationRecord`

Represents persisted youbot conversation history.

```python
conversation_id: str
messages: list[ConversationMessage]
updated_at: str
last_response_id: str | None
```

### `UsageReviewBundle`

Represents a bounded developer-facing snapshot of how this installation of youbot has been used.

```python
bundle_id: str
created_at: str
source_state_root: str
window_summary: str
conversation_id: str | None
messages: list[ConversationMessage]
command_runs: list[dict]
coding_agent_runs: list[dict]
activity_entries: list[dict]
activity_log_refs: list[str]
notes: list[str]
```

Invariants:
- A bundle is derived review data, not the primary source of truth
- A bundle must be bounded in size and time window
- A bundle is intended for review of the `youbot` repo itself, not as ambient context for arbitrary child-repo coding work

### `RouteDecision`

The router's structured output.

```python
repo_id: str | None
action_type: Literal["command", "query", "code_change", "adapter_change", "clarify", "global_action"]
command_name: str | None
arguments: list[str]
reasoning_summary: str
confidence: float
```

Invariants:
- `command_name` is required when `action_type == "command"`
- `repo_id` may be `None` only for global actions or clarifications
- `confidence` is normalized to `0.0 <= x <= 1.0`
- `action_type == "adapter_change"` targets youbot-owned adapter/view behavior rather than child-repo code

### `CodingAgentBackend`

Represents the configured backend for code-change work.

```python
backend_name: Literal["claude_code", "codex"]
command_prefix: list[str]
default_args: list[str]
```

Invariants:
- `command_prefix` is executable on the host
- callers do not branch on backend-specific shell details outside the runner

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

### `CodingAgentResult`

Represents a completed coding-agent invocation.

```python
repo_id: str
backend_name: Literal["claude_code", "codex"]
exit_code: int
stdout: str
stderr: str
started_at: str
finished_at: str
duration_ms: int
```

### `CodingAgentSessionRef`

Represents a backend-native resumable coding-agent session for a repo.

```python
repo_id: str
backend_name: Literal["claude_code", "codex"]
session_kind: Literal["noninteractive"]
session_id: str
purpose_summary: str | None
status: Literal["active", "stale", "unknown"]
last_used_at: str
```

Invariants:
- `session_id` is a backend-native continuation handle
- `session_kind` is automation-compatible and non-interactive for youbot-driven runs
- youbot stores the handle and minimal metadata, not the full coding-agent transcript

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
overview_sections: list[OverviewSectionSpec]
quick_actions: list[QuickActionSpec]
```

### `OverviewSectionSpec`

Represents generated adapter metadata for the selected-repo overview panel.

```python
command_name: str
arguments: list[str]
title: str | None
max_lines: int
fallback_command_names: list[str]
render_mode: Literal["json", "text"]
```

### `QuickActionSpec`

Represents a recommended action for the selected-repo workspace.

```python
command_name: str
title: str | None
arguments: list[str]
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

Behavioral rules:
- `register_repo(...)` persists the repo into user config
- registration triggers command discovery and adapter generation
- integrated repo registration requires only a valid path and `justfile`

### `ConversationStore`

Responsibilities:
- Persist youbot conversation history
- Append messages
- Load recent history for routing

Suggested methods:

```python
get_conversation() -> ConversationRecord
append_message(message: ConversationMessage) -> None
clear_conversation() -> None
set_last_response_id(response_id: str | None) -> None
```

### `UsageReviewService`

Responsibilities:
- Read bounded usage history from youbot-owned runtime state
- Build a developer-facing review bundle for analysis of the `youbot` repo
- Avoid exposing unbounded raw history by default

Suggested methods:

```python
build_bundle(
    *,
    max_messages: int = 200,
    max_command_runs: int = 100,
    max_coding_agent_runs: int = 100,
) -> UsageReviewBundle
write_bundle(bundle: UsageReviewBundle) -> str
```

Behavioral rules:
- The service reads from `~/.youbot/` state rather than from user config
- The service may include references to raw files, but the bundle remains the preferred review surface
- The service should trim or summarize oversized payloads rather than reproducing unbounded logs verbatim

### `OpenAIChatOrchestrator`

Responsibilities:
- Run the primary chat loop through the OpenAI Responses API
- Provide tool definitions over repo metadata and execution surfaces
- Continue provider-native conversational state with `last_response_id`

Suggested method:

```python
respond(
    *,
    user_message: str,
    active_repo_id: str | None,
    repos: list[RepoRecord],
    commands: dict[str, list[CommandRecord]],
    last_response_id: str | None,
    tool_handler: Callable[[str, dict], dict],
) -> tuple[str, str | None]
```

### `CodingAgentSessionRegistry`

Responsibilities:
- Persist repo-specific coding-agent session references
- Resolve the last known backend-native session for a repo

Suggested methods:

```python
get_session(repo_id: str) -> CodingAgentSessionRef | None
set_session(session: CodingAgentSessionRef) -> None
clear_session(repo_id: str) -> None
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
    conversation: ConversationRecord,
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

### `CodingAgentRunner`

Responsibilities:
- Invoke the configured coding-agent backend for code-change requests

Suggested methods:

```python
get_backend(repo_id: str | None = None) -> CodingAgentBackend
run_code_change(
    repo: RepoRecord,
    request: str,
    context: str | None = None,
) -> CodingAgentResult
```

Behavioral rules:
- Claude Code runs should use non-interactive scripting-compatible forms
- Codex runs should use non-interactive forms such as `codex exec` / `codex exec resume`
- Interactive resume pickers are never part of the orchestration path

### Developer command contract: `review-usage`

Purpose:
- Provide an explicit way for the coding agent working on `youbot` to inspect recent real usage of this installation

Suggested behavior:

```python
review_usage(
    *,
    max_messages: int = 200,
    max_command_runs: int = 100,
    max_coding_agent_runs: int = 100,
) -> tuple[str, str]
```

Return value:
- A human-readable summary of what was reviewed
- The path to the generated review bundle

Behavioral rules:
- The command is developer-facing and specific to the `youbot` repo
- The command reads from youbot-owned runtime state under `~/.youbot/`
- The command generates a bounded review artifact before invoking or informing the coding agent
- The command should not silently inject the full raw transcript into unrelated coding-agent prompts

### `AdapterLoader`

Responsibilities:
- Load local adapter definitions for a repo
- Provide palette entries and output rendering rules
- Generate adapter metadata during onboarding or refresh

Suggested methods:

```python
load(repo_id: str) -> AdapterRecord | None
save(adapter: AdapterRecord) -> None
refresh(repo: RepoRecord, commands: list[CommandRecord]) -> AdapterRecord
```

## Ownership rules

- The registry owns repo and command metadata.
- The conversation store owns youbot conversation history.
- The coding-agent session registry owns backend-native session references.
- The adapter loader owns adapter definitions and rendering hints.
- The executor owns subprocess execution details.
- The coding-agent runner owns backend selection and backend-specific invocation details.
- The TUI owns presentation, not domain decisions.
- The OpenAI chat orchestrator owns the primary conversational decision path.
- The router owns fallback repo/action selection when the primary path is unavailable.

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
