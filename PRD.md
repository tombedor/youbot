# youbot PRD

## Overview

Youbot is a stateful conversational agent and TUI that orchestrates a collection of specialized Python repos. The primary interface is natural language: you describe what you want, and youbot figures out which repo is relevant, what action to take, and whether that action requires running an existing command, querying data, or changing code.

Youbot is not a file browser or a code editor. For browsing code, open the repo directly. Youbot's value is in surfacing data from your repos, triggering their capabilities, and requesting changes to them — all from a single interface, in plain language.

---

## Interaction Model

### Conversational interface

The TUI is primarily a conversation pane with rich inline output (tables, lists, structured data). The session is stateful — context from earlier in the conversation is preserved and can be referenced.

Examples:
- "what's on my to-do list?" → routes to life_admin, queries data, renders inline
- "show me the job openings from yesterday" → routes to job_search, queries DB, renders table
- "those openings — filter to remote only" → refers back to previous result, re-queries
- "run a job search" → routes to job_search, runs `just search`
- "don't show me cryptocurrency companies" → routes to job_search, determines action (see Change Request Flow)

### Change request flow

When a change is requested:

1. Check whether an existing `just` command covers the use case. If so, run it.
2. If not, spawn a `claude` subprocess in the target repo's directory with the request.
3. After the change, evaluate whether this is likely to be requested again. If so, add a new `just` command that covers it.

The justfile is the canonical capability registry for each repo. If a capability is worth having, it should be expressible as a `just` command so both humans and agents can reach it without going through the conversational interface.

### Routing

Youbot routes requests by calling the Claude API with:
- The user's message and conversation history
- The list of registered repos, their PRD summaries, and their available `just` commands

Claude determines: which repo is relevant, what type of action is needed (query, command, code change), and what parameters to pass.

---

## Architecture

### Youbot

- Python package: `youbot`
- Textual TUI: conversation pane + repo status sidebar
- Plugin loader: discovers and loads `youbot_plugin.py` from each registered repo
- Scheduler: runs `just` commands on configured schedules
- Agent spawner: runs `claude` as a subprocess in a repo directory

### Plugin interface

Each repo exposes a `YoubotPlugin` in its `youbot_plugin.py`:

```python
class YoubotPlugin:
    name: str                    # human-readable repo name
    repo_path: str               # absolute path to repo root
    screen: Screen               # Textual Screen for structured views
    commands: CommandProvider    # Textual CommandProvider for this repo
```

### Command palette

Textual's command palette supports multiple `CommandProvider` instances. Youbot uses this to keep commands context-sensitive:

- A **global provider** is always active: switch repo, initialize new repo, youbot-level settings.
- Each plugin's `CommandProvider` is only active when that plugin's screen is focused.

When in the job_search view, the palette shows job_search commands plus globals. Switch to life_admin and the palette swaps. No cross-repo noise.

Plugin commands can be a mix of:
- Wrappers around `just` commands (auto-discovered from the justfile)
- UI-only actions that have no CLI equivalent (e.g., opening a sub-view, filtering the current table)

Youbot also discovers available `just` commands by reading the repo's justfile directly, for use in routing and the change request flow.

### Data layer pattern

Each repo's data logic lives in its Python package and is consumed by two independent surfaces:

- **CLI / just commands**: shell into the package's CLI module (`python -m repo.cli`)
- **Textual plugin**: imports the package's data layer directly

This ensures the CLI and UI are always consistent because they share the same underlying code.

---

## Sub-repo Contract

Every repo integrated into youbot MUST conform to this contract. These are hard requirements, not suggestions.

### Required files

| File | Purpose |
|------|---------|
| `PRD.md` | What this repo does and why. Must be kept current. |
| `AGENTS.md` | Instructions for coding agents working in this repo. Coding style, constraints, architectural decisions. |
| `CAPTAINS_LOG.md` | Append-only log of meaningful changes, task results, and decisions. Entries are dated. |
| `justfile` | All user-facing and agent-facing capabilities. Must include at minimum: `test`, `lint`, `format`. |
| `youbot_plugin.py` | Plugin entry point for youbot integration. |
| `pyproject.toml` | Package definition. |

### Code quality requirements

**Typing**
- All functions must have type annotations. No `Any` except where genuinely unavoidable.
- Mypy must pass with `strict = true`.

**Linting and formatting**
- Ruff for linting and formatting. Config in `pyproject.toml`.
- `just lint` must exit 0 before any commit.
- `just format` must be idempotent.

**Tests**
- Pytest. `just test` must exit 0.
- Tests must cover the data layer. CLI and plugin integration can be lighter.
- No tests that hit external APIs without mocking.

**Structure**
- Data layer (`db.py`, `models.py`, etc.) must be importable independently of CLI and UI.
- No business logic in CLI entrypoints or Textual components.
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
- A `youbot_plugin.py` stub

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
- Any repo that does not conform to the sub-repo contract.
