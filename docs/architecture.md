# Youbot Architecture

## Purpose

This document translates the product requirements in `docs/PRD.md` into a concrete system design. It is intended to constrain implementation choices so a coding agent can build the system in bounded slices without re-deciding the architecture.

## System boundaries

Youbot is a local Python application with a Textual TUI. It orchestrates a set of registered repos by:

- Discovering and parsing each repo's `justfile`
- Persisting repo metadata and conversation state in youbot-owned storage
- Routing natural-language requests to the correct repo and execution mode
- Running `just` commands in repo directories
- Spawning `claude` for code-change requests when no existing command fits
- Rendering repo-specific views through youbot-owned adapters

Integrated repos are treated as capability providers. They are not required to embed UI code or conform to youbot's internal architecture.

## Core modules

The initial implementation should be organized around these modules:

### `registry`

Responsibilities:
- Load configured repos from youbot config
- Validate that a repo has a usable `justfile`
- Store and retrieve repo metadata
- Persist discovered commands, tags, summaries, routing hints, and repo classification

Key rule:
- The registry is the source of truth for repo metadata inside youbot.

### `sessions`

Responsibilities:
- Persist one global session
- Persist one current session per repo
- Support reset and branching semantics later
- Provide conversation history to the router

Key rule:
- Session state is scoped, not global by default.

### `justfile_parser`

Responsibilities:
- Discover available `just` recipes
- Extract recipe names and, where possible, descriptions or inline comments
- Normalize command metadata into a canonical internal representation

Key rule:
- Parser output feeds both routing and command-palette generation.

### `router`

Responsibilities:
- Assemble routing context from user message, session history, repo metadata, and discovered commands
- Call the model to choose repo, action type, and parameters
- Return a structured route decision, not free-form text

Key rule:
- The router decides intent; execution modules do not reinterpret the user's request.

### `executor`

Responsibilities:
- Run `just <recipe>` in the selected repo
- Capture stdout, stderr, exit status, duration, and parsed structured output
- Return normalized execution results for UI rendering and session logging

Key rule:
- Command execution is the default path when a matching capability exists.

### `agent_spawner`

Responsibilities:
- Spawn `claude` in the target repo for code-change requests
- Provide request context and capture subprocess outcome
- Record the result in session state and registry hints

Key rule:
- This path is only used when no suitable `just` command exists or when the router explicitly chooses code change.

### `adapters`

Responsibilities:
- Load youbot-owned repo adapters from local state
- Provide repo-specific command palette entries
- Map command output into Textual views
- Hold parsing and presentation hints

Key rule:
- Adapters belong to youbot, not to the child repos.

### `scheduler`

Responsibilities:
- Execute configured recurring `just` commands
- Log results to youbot state
- Surface recent scheduled activity in the UI

Key rule:
- Scheduling configuration lives in youbot, never in child repos.

### `tui`

Responsibilities:
- Render the conversation pane
- Render repo list/status sidebar
- Manage repo focus and screen switching
- Expose global and repo-scoped command palette actions
- Display execution results and structured views

Key rule:
- The TUI is a consumer of registry, sessions, routing, and adapters. It should not own business logic.

## Persistence model

Youbot owns its application state. Child repos remain external systems.

Expected state areas:

- Config:
  - registered repos
  - scheduler configuration
  - user preferences
- Registry store:
  - repo records
  - discovered commands
  - routing hints
  - adapter metadata
- Session store:
  - global conversation history
  - per-repo conversation history
- Adapter store:
  - local adapter code or adapter definitions
  - parser hints
  - view configuration
- Execution history:
  - recent commands
  - exit status
  - timestamps

The exact on-disk format can be JSON or SQLite in the first version. The implementation should pick one format and use it consistently.

## Main runtime flows

### 1. Repo onboarding

1. User adds a repo path.
2. Registry validates presence of `justfile`.
3. `justfile_parser` discovers commands.
4. Registry stores repo metadata and initial command inventory.
5. Adapter loader creates or refreshes local adapter metadata.
6. Repo becomes available in the TUI.

### 2. Resume session

1. Youbot starts.
2. Registry loads registered repos.
3. Session manager loads the global session and repo sessions.
4. TUI opens with the last active repo or a default global view.
5. Switching into a repo restores that repo's conversation context.

### 3. Natural-language request

1. User submits a message.
2. TUI sends the message plus active scope to the router.
3. Router reads relevant session history and registry metadata.
4. Router returns a structured route decision.
5. If action type is `command`, executor runs the selected `just` recipe.
6. If action type is `code_change`, agent spawner runs `claude` in the repo.
7. Result is rendered in the TUI and appended to the relevant session.

### 4. Command-palette action

1. User opens the command palette.
2. Global commands are always available.
3. If a repo is focused, the active adapter contributes repo-specific commands.
4. Selected command invokes executor or a UI-only adapter action.

## Error handling

The system should treat these as expected operational cases:

- Missing or invalid `justfile`
- Repo path no longer exists
- `just` executable missing on the host
- Recipe exits non-zero
- Command output is not parseable as structured data
- Router returns an invalid decision
- `claude` subprocess fails or is unavailable

Initial error-handling rules:

- Show failures inline in the conversation pane
- Preserve raw stderr for inspection
- Do not destroy session state on failure
- Mark affected repo status in the registry

## Non-goals for v1

- Editing child-repo UI code
- Deep semantic parsing of arbitrary shell output
- Multi-user synchronization
- Remote orchestration
- Strong plugin sandboxing

## Recommended package layout

One reasonable initial package shape is:

```text
youbot/
  __init__.py
  app.py
  config.py
  registry.py
  sessions.py
  justfile_parser.py
  router.py
  executor.py
  agent_spawner.py
  adapters/
    __init__.py
    loader.py
    models.py
  tui/
    __init__.py
    app.py
    screens.py
    widgets.py
    command_palette.py
```

This layout is not mandatory, but the separation of concerns is.
