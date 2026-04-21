# youbot PRD

## Overview

Youbot is a stateful conversational agent and TUI that orchestrates a collection of specialized Python repos. The primary interface is natural language: you describe what you want, and youbot figures out which repo is relevant, what action to take, and whether that action requires running an existing command, querying data, or changing code.

Youbot is not a file browser or a code editor. For browsing code, open the repo directly. Youbot's value is in surfacing data from your repos, triggering their capabilities, and requesting changes to them — all from a single interface, in plain language.

V1 is repo-first because that matches the primary personal-workflow use case. The architecture should remain extensible enough to support non-repo CLI-backed integrations later, but repos are the initial unit of organization and focus.

---

## Interaction Model

Detailed user-driven flows are documented in `docs/user_stories.md`.

### Conversational interface

The TUI is primarily a conversation pane with rich inline output (tables, lists, structured data). It starts in a global chat state with no repo selected by default. Youbot keeps lightweight conversation history so earlier interactions can inform follow-up actions.

Youbot itself does not need to maintain a separate persistent chat session for each repo in v1. Repo focus in the UI biases tool use, command discovery, and displayed views, but it does not imply a distinct repo-scoped youbot transcript.

Primary chat orchestration should use the OpenAI API with tool calls. The chat model should inspect registered repos, list commands, run repo commands, and trigger code-change work through explicit tool calls rather than relying only on a local heuristic router.

For code-change work, youbot should continue backend-native coding-agent sessions when possible. Each repo may have an associated Claude Code or Codex session reference that youbot can reuse instead of reconstructing history itself.

Youbot should only drive automation-compatible, non-interactive coding-agent invocations. It should not depend on interactive pickers or interactive terminal session management inside Claude Code or Codex.

Examples:
- "what's on my to-do list?" → routes to life_admin, queries data, renders inline
- "show me the job openings from yesterday" → routes to job_search, queries DB, renders table
- "those openings — filter to remote only" → refers back to previous result, re-queries
- "run a job search" → routes to job_search, runs `just search`
- "don't show me cryptocurrency companies" → routes to job_search, determines action (see Change Request Flow)

### Change request flow

When a change is requested:

1. Check whether an existing `just` command covers the use case. If so, run it.
2. If not, invoke the configured coding-agent backend in the target repo's directory with the request, resuming an existing backend-native non-interactive session when appropriate.
3. After the change, evaluate whether this is likely to be requested again. If so, add a new `just` command that covers it.

The justfile is the canonical capability registry for each repo. If a capability is worth having, it should be expressible as a `just` command so both humans and agents can reach it without going through the conversational interface.

The coding-agent backend must be configurable. Initial supported backends:
- Claude Code
- Codex

Switching between coding-agent backends should be a configuration change, not an architectural rewrite.

### Tool-driven orchestration

Primary chat should call a model with:
- The user's message
- Recent youbot conversation context
- The list of registered repos, their youbot-managed metadata, and their available `just` commands
- A tool surface for inspecting repos and executing actions

The model determines which repo is relevant, what type of action is needed, and which tool calls to make. A simpler local heuristic router may exist as fallback behavior when the OpenAI-backed primary path is unavailable, but it is not the main orchestration design.

---

## Architecture

### Youbot

- Python package: `youbot`
- Textual TUI: conversation pane + repo status sidebar
- Repo registry: stores repo metadata, discovered commands, routing hints, coding-agent session references, and adapter configuration
- Adapter loader: discovers and loads youbot-owned adapters for registered repos
- Scheduler: runs `just` commands on configured schedules
- Coding-agent runner: invokes the configured coding-agent backend in a repo directory
- Conversation store: persists lightweight youbot conversation history
- Coding-agent session registry: persists backend-native session references per repo
- Agent backend config: stores backend selection and backend-specific invocation settings

### Repo adapter model

Youbot owns the TUI code that renders repo-specific views. Integrated repos are not required to ship Textual code.

For each registered repo, youbot maintains a local adapter in its own state directory. Adapters may be generated, cached, or manually refined over time, but they live in youbot's local plugin/adapter registry rather than in the child repo.

Repo onboarding includes an adapter generation step. At minimum, youbot generates adapter metadata that picks an overview command for the selected-repo workspace, basic rendering limits, and any fallback commands.

An adapter may contain:
- Repo identity and source location
- Discovered `just` commands
- Generated overview-command metadata for the selected-repo workspace
- Command descriptions and invocation hints
- Structured view definitions for the TUI
- Output parsing/rendering logic
- Routing hints based on successful prior usage

### Command palette

Textual's command palette supports multiple `CommandProvider` instances. Youbot uses this to keep commands context-sensitive:

- A **global provider** is always active: switch repo, initialize new repo, youbot-level settings.
- Each repo adapter's `CommandProvider` is only active when that repo's screen is focused.

When in the job_search view, the palette shows job_search commands plus globals. Switch to life_admin and the palette swaps. No cross-repo noise.

Adapter commands can be a mix of:
- Wrappers around `just` commands (auto-discovered from the justfile)
- UI-only actions that have no CLI equivalent (e.g., opening a sub-view, filtering the current table)

Youbot also discovers available `just` commands by reading the repo's justfile directly, for use in routing and the change request flow.

### Data layer pattern

Integrated repos expose capabilities through `just` commands. Youbot consumes those capabilities and renders its own UI around them.

Managed repos created by youbot should still keep data logic in the Python package and keep business logic out of CLI entrypoints, but that is a managed-repo standard rather than a universal integration requirement.

---

## Repo Integration Model

Youbot supports two classes of repos:

### Integrated repos

Integrated repos are repos youbot can inspect and invoke. They may be read-only or externally managed.

Minimum contract:
- `justfile`

That is the only required artifact for integration. If a repo exposes callable `just` commands, youbot can use it.

Additional metadata for integrated repos is stored by youbot, not required from the repo itself.

First-class onboarding should:
- register the repo into youbot config
- validate the repo path and `justfile`
- scan the repo's commands
- generate initial adapter metadata and artifacts
- make the repo immediately available in the TUI and CLI

### Youbot-managed repo metadata

For each integrated repo, youbot may store:
- Human-readable repo name
- Repo path
- Short purpose description
- Tags
- Discovered `just` commands
- Command descriptions and preferred commands
- Output handling hints and parser configuration
- Routing hints and examples of successful prompts
- Repo classification (`integrated` vs `managed`)
- Last active coding-agent backend
- Coding-agent session reference, if the backend supports continuation
- Coding-agent session kind (`noninteractive` by default for youbot-driven runs)
- Adapter/plugin state for local TUI rendering
- Preferred coding-agent backend override, if different from the global default

This metadata lives in youbot's own registry and state directory. It is not checked into the child repo by default.

### Managed repos

Managed repos are repos created by youbot or explicitly brought under youbot's stricter standards. These repos are expected to conform to a higher-quality scaffold because youbot has edit authority and ownership over their conventions.

Required files:

| File | Purpose |
|------|---------|
| `PRD.md` | What this repo does and why. Must be kept current. |
| `AGENTS.md` | Instructions for coding agents working in this repo. Coding style, constraints, architectural decisions. |
| `CAPTAINS_LOG.md` | Append-only log of meaningful changes, task results, and decisions. Entries are dated. |
| `justfile` | All user-facing and agent-facing capabilities. Must include at minimum: `test`, `lint`, `format`. |
| `pyproject.toml` | Package definition. |

Code quality requirements:

**Typing**
- All functions must have type annotations. No `Any` except where genuinely unavoidable.
- Mypy must pass with `strict = true`.

**Linting and formatting**
- Ruff for linting and formatting. Config in `pyproject.toml`.
- `just lint` must exit 0 before any commit.
- `just format` must be idempotent.

**Tests**
- Pytest. `just test` must exit 0.
- Tests must cover the data layer.
- No tests that hit external APIs without mocking.

**Structure**
- Data layer (`db.py`, `models.py`, etc.) must be importable independently of CLI and UI.
- No business logic in CLI entrypoints.
- SQLite for local persistence unless there is a specific reason otherwise. Document the reason in `PRD.md`.

**Justfile**
- Required commands: `test`, `lint`, `format`, `install`
- Commands must be runnable from a clean checkout after `just install`.
- Commands that produce data output should support `--format=json` for programmatic consumption.

**AGENTS.md**
- Must describe the architectural decisions a coding agent needs to know before making changes.
- Must list gotchas, constraints, and patterns used in the codebase.
- Must be updated when significant patterns change.

**CAPTAINS_LOG.md**
- Every meaningful change gets a dated entry.
- Task results (search runs, trade outcomes, etc.) are logged here when relevant.
- Entries are append-only. Do not edit past entries.

### Initialization

When youbot initializes a new repo, it scaffolds:
- All required files with sensible stubs
- `pyproject.toml` with ruff, mypy, and pytest configured to the above standards
- A justfile with the required commands wired up

New repos may be initialized by the user via the TUI or by youbot autonomously when a new capability is identified.

---

## Registered repos

Initial set:

| Repo | Path | Purpose |
|------|------|---------|
| job_search | `~/development/job_search` | Track job openings, application status, run searches |
| life_admin | `~/development/life_admin` | To-do list, personal admin tasks |
| trader_bot | `~/development/trader_bot` | Prediction market trades (Kalshi) |
| notes | `~/development/notes` | Vector index over Obsidian notes |

---

## Scheduling

Youbot maintains a schedule of recurring `just` commands across repos. Schedules are defined in youbot's config, not in the repos themselves, since scheduling is a concern of the orchestrator.

Example: `job_search: just search` runs nightly.

---

## Out of scope

- File browsing. Open the repo in your editor.
- Multi-user or remote access.
- Managing repos that do not expose a usable `justfile`.
