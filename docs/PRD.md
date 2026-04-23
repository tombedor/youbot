# youbot PRD

## Overview

Youbot is a stateful conversational agent and TUI that orchestrates a collection of specialized repos. The primary interface is natural language: you describe what you want, and youbot figures out which repo is relevant, what action to take, and whether that action requires running an existing command, querying data, or changing code.

Youbot is not a file browser or a code editor. For browsing code, open the repo directly. Youbot's value is in surfacing data from your repos, triggering their capabilities, and requesting changes to them — all from a single interface, in plain language.

V1 is repo-first because that matches the primary personal-workflow use case. The architecture should remain extensible enough to support non-repo CLI-backed integrations later, but repos are the initial unit of organization and focus.

### Language boundary

This PRD is intended to be language-agnostic by default. Product requirements should describe user-visible behavior, integration contracts, routing behavior, and ownership boundaries in ways that apply regardless of whether an integrated repo is implemented in Python, TypeScript, Go, Rust, or another language.

Language-specific details belong only in clearly marked implementation-profile sections. In particular:
- Integrated repos are defined by the commands they expose and the outputs they produce, not by their implementation language.
- Managed-repo standards should default to language-neutral requirements unless a language-specific profile is explicitly called out.
- The current youbot implementation may use Python and Textual, but those choices are implementation details, not the product contract for repo integration.

---

## Interaction Model

Detailed user-driven flows are documented in `docs/user_stories.md`.

### Conversational interface

The TUI uses a simple three-region shell: one chat panel, one dismissable sidebar, and one repo panel only when a repo is active. It starts in a global chat state with no repo selected by default. When no repo is selected, the repo panel is omitted entirely. Youbot keeps lightweight conversation history so earlier interactions can inform follow-up actions.

When youbot is processing a user message, the UI must show a visible in-flight indicator in the chat area so the user can tell the request is actively being handled. A spinner or equivalent loading treatment is sufficient; silent waiting is not.

When youbot launches a coding-agent run, the UI must also expose a live activity view for that run. The user should be able to see that a coding session has started, which backend and target it is using, and incremental log/output updates while the run is in progress. A completed summary alone is not sufficient for longer-running coding work.

The UI must also be able to surface a routing-trace pane for the active chat turn. This pane should show a decision tree of what the chat router or orchestrator has already done, what branches or decisions remain ahead, and what step is currently in progress. The trace is an observability surface for the user; it should explain the work without requiring inspection of raw logs.

When a repo is selected, the single repo panel should present a compact repo-specific header, a purpose-built overview layout, and adapter-defined quick actions. It should not feel like a generic stack of undifferentiated panels, and the shell should not create additional persistent panels for repo overview content.

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
2. Determine whether the change targets a child repo's implementation or a youbot-owned adapter/view.
3. If the request is about how a repo is presented inside youbot's TUI, route the change to the relevant adapter/plugin in youbot-owned state by default rather than editing the child repo.
4. If the request is about the child repo's own commands, data model, business logic, or outputs, invoke the configured coding-agent backend in that repo's directory, resuming an existing backend-native non-interactive session when appropriate.
5. If the target is ambiguous, ask a clarification question before making changes.
6. After an adapter/view change, reload the affected selected-repo workspace so the updated presentation is visible without restarting the app.
7. After the change, evaluate whether this is likely to be requested again. If so, add a new `just` command that covers it when the capability belongs in the child repo rather than the adapter layer.

The justfile is the canonical capability registry for each repo. If a capability is worth having, it should be expressible as a `just` command so both humans and agents can reach it without going through the conversational interface.

For the `youbot` repo itself, developer-facing commands may also inspect youbot-owned runtime state to improve the product. In particular, a repo-local `review-usage` command should gather recent transcript and operational history from this installation's `~/.youbot/` state, build a bounded review artifact, and make that artifact available to the coding agent working on `youbot`.

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

### Developer review flow for the `youbot` repo

When working on the `youbot` repo itself, the coding agent should be able to inspect how this installation of youbot has actually been used.

This should happen through an explicit developer-facing review command rather than by silently injecting the entire transcript into every coding run.

The `review-usage` flow should:

1. Read a bounded slice of youbot-owned runtime state from `~/.youbot/`.
2. Include recent conversation history, command runs, coding-agent runs, and any available live activity/log records.
3. Write a derived review bundle for the current review invocation.
4. Invoke the coding agent on the `youbot` repo with instructions to analyze that bundle and suggest concrete product, routing, adapter, and UX improvements.

The review bundle is the preferred analysis surface. Raw state files remain the source of truth, but they should not be treated as implicit background prompt context for unrelated coding work.

---

## Current implementation profile

### Youbot

- Python package: `youbot`
- Textual TUI: one chat panel + dismissable repo status sidebar + optional active-repo panel
- Repo registry: stores repo metadata, discovered commands, routing hints, coding-agent session references, and adapter configuration
- Adapter loader: discovers and loads youbot-owned adapters for registered repos
- Scheduler: runs `just` commands on configured schedules
- Coding-agent runner: invokes the configured coding-agent backend in a repo directory
- Conversation store: persists lightweight youbot conversation history
- Routing-trace store: persists or publishes structured per-turn routing/orchestration trace state for UI inspection
- Coding-agent session registry: persists backend-native session references per repo
- Agent backend config: stores backend selection and backend-specific invocation settings
- Usage review flow: generates bounded review bundles from youbot-owned runtime state for developer analysis of the `youbot` repo

### Repo adapter model

Youbot owns the UI code that renders repo-specific views. Integrated repos are not required to ship UI-framework-specific integration code.

For each registered repo, youbot maintains a local adapter in its own state directory. Adapters may be generated, cached, or manually refined over time, but they live in youbot's local plugin/adapter registry rather than in the child repo.

This separation is user-visible and must affect routing. A request to change how `life_admin` appears inside youbot is, by default, a request to change the `life_admin` adapter in youbot-owned state rather than a request to edit the `life_admin` repo itself.

Repo onboarding includes an adapter generation step. At minimum, youbot generates adapter metadata that picks overview sections for the selected-repo workspace, basic rendering limits, preferred render modes, and any fallback commands.

Adapters should also define a small set of recommended quick actions for the selected-repo workspace so the UI can highlight the most useful commands instead of dumping a long raw command list.

When a repo exposes JSON-capable commands, adapters should prefer those structured outputs for the selected-repo workspace so the view can emphasize the most relevant information rather than dumping raw markdown or raw text.

When an adapter is updated, youbot should refresh the active selected-repo workspace from the updated adapter state so UI changes are visible immediately.

An adapter may contain:
- Repo identity and source location
- Discovered `just` commands
- Generated overview-section metadata for the selected-repo workspace
- Command descriptions and invocation hints
- Structured view definitions for the TUI
- Output parsing/rendering logic
- Routing hints based on successful prior usage

### Command palette

The command palette should support multiple provider scopes. Youbot uses this to keep commands context-sensitive:

- A **global provider** is always active: switch repo, initialize new repo, youbot-level settings.
- Each repo adapter's `CommandProvider` is only active when that repo's screen is focused.

When in the job_search view, the palette shows job_search commands plus globals. Switch to life_admin and the palette swaps. No cross-repo noise.

Adapter commands can be a mix of:
- Wrappers around `just` commands (auto-discovered from the justfile)
- UI-only actions that have no CLI equivalent (e.g., opening a sub-view, filtering the current table)

Youbot also discovers available `just` commands by reading the repo's justfile directly, for use in routing and the change request flow.

### Data layer pattern

Integrated repos expose capabilities through `just` commands. Youbot consumes those capabilities and renders its own UI around them.

Managed repos created by youbot should still keep core application logic separate from CLI entrypoints, but that is a managed-repo standard rather than a universal integration requirement.

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
- validate the repo path and `justfile`
- scan the repo's commands
- generate initial repo metadata (purpose summary, recommended show command, suggested overview sections)
- present the generated metadata to the user for review and allow iteration before persisting
- on user approval, register the repo into youbot config and persist the confirmed metadata
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
| language/toolchain manifest | The repo's native dependency or build manifest, such as `pyproject.toml`, `package.json`, `Cargo.toml`, or `go.mod`. |

Code quality requirements:

**Interfaces and typing**
- Public interfaces should be explicit and machine-checkable in the native toolchain where practical.
- If the language supports static typing or interface checking, the repo should use it for public boundaries unless there is a documented reason not to.

**Linting and formatting**
- The repo must define formatter and linter commands appropriate to its language and toolchain.
- `just lint` must exit 0 before any commit.
- `just format` must be idempotent.

**Tests**
- `just test` must exit 0.
- Tests must cover the data layer or domain core where the repo keeps its durable logic.
- No tests should hit external APIs without an explicit mock, fixture, or isolated integration environment.

**Structure**
- Core logic should be importable or callable independently of CLI and UI entrypoints.
- No business logic in CLI entrypoints.
- If the repo owns local persistence, its storage choice and rationale must be documented in `PRD.md`.

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

For the `youbot` managed repo specifically, developer-oriented commands may also operate on youbot-owned runtime state outside the repo when that state is necessary to improve the orchestrator itself. `review-usage` is the primary example.

### Python implementation profile for managed repos

If a managed repo is implemented in Python, the preferred default profile is:
- `pyproject.toml` as the toolchain manifest
- Ruff for linting and formatting
- Mypy in strict mode where practical
- Pytest for tests
- Repo-local structural-size checks when module growth needs active enforcement

### Initialization

When youbot initializes a new repo, it scaffolds:
- All required files with sensible stubs
- the native language/toolchain manifest with formatter, linter, and test tooling configured to the above standards
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
