# Milestones

## Purpose

This document defines the recommended implementation order. Each milestone should produce a usable vertical slice and should be completable without speculative work on later milestones.

## Milestone 1: Repo registry and command discovery

Goal:
- Register repos, validate `justfile`, and parse commands into canonical records.

Includes:
- config loading for registered repo paths
- repo validation
- `justfile` parsing
- in-memory or persisted registry storage

Done when:
- youbot can load the configured repos at startup
- repos without a usable `justfile` are rejected or marked invalid
- discovered commands are visible through a simple debug output or test

Non-goals:
- TUI rendering
- routing
- session persistence

## Milestone 2: Conversation, task, and session state

Goal:
- Persist youbot conversation history, explicit task records, and repo-specific coding-agent session references.

Includes:
- conversation store
- task store
- coding-agent session registry
- append/read operations
- startup restore behavior
- active repo tracking

Done when:
- a user interaction can be recorded in youbot conversation history
- a repo can store a coding-agent session reference with `tmux` metadata
- a unit of work can be represented as a task
- restarting the app restores conversation history, tasks, and coding-agent session references

Non-goals:
- reconstructing full coding-agent transcripts
- session branching UI

## Milestone 3: Coding-session launch and attach

Goal:
- Launch or resume coding-agent work inside `tmux` and expose attachment details.

Includes:
- `tmux` session creation and lookup
- coding-agent backend launch in repo directory
- session registry updates
- attach-command generation

Done when:
- a repo code-change task starts a backend in a named `tmux` session
- the stored session record includes enough metadata to reattach later
- a user can obtain the command needed to attach to that running session

Non-goals:
- full TUI shell
- routing

## Milestone 4: Minimal Textual shell

Goal:
- Bring up the TUI with repo switching, conversation display, task visibility, and session attachment affordances.

Includes:
- app shell
- repo sidebar
- active repo selection
- basic conversation display
- basic task list
- active-session attach actions

Done when:
- the user can see the configured repos
- switching repos changes active focus and available commands
- stored conversation history is rendered
- active tasks and active coding sessions are visible

Non-goals:
- routing
- structured data views

## Milestone 5: Command execution path

Goal:
- Execute selected `just` commands inside the active repo and render results.

Includes:
- executor
- basic command palette integration
- result capture and display
- task updates for command work

Done when:
- a repo command can be launched from the UI
- stdout, stderr, and exit status are surfaced
- execution events are appended to the relevant task history

Non-goals:
- natural-language routing
- adapter rendering beyond basic text

## Milestone 6: Scheduling

Goal:
- Execute configured recurring commands and surface their results.

Includes:
- scheduler config
- recurring job runner
- recent job status display
- task or run-history integration for scheduled work

Done when:
- a scheduled `just` command runs without manual intervention
- the result is stored and visible in the UI
- scheduled work appears in recent task or scheduler history

## Milestone 7: Primary chat orchestration

Goal:
- Route natural-language requests through the primary chat orchestrator to repo + action + command.

Includes:
- OpenAI Responses API integration
- tool definition and tool execution loop
- concise final answer generation
- routing-trace production for in-flight decision visibility
- fallback behavior for low confidence or unavailable API

Done when:
- a natural-language request selects the correct repo in common cases
- command requests execute without manual command selection
- low-confidence routes surface a clarification path instead of guessing blindly
- the UI can surface a per-turn routing trace that distinguishes completed, current, and pending steps

Non-goals:
- code-change flow
- learned routing improvements

## Milestone 8: Code-change flow

Goal:
- Invoke a configurable coding-agent backend inside a repo when no existing command satisfies the request, using the managed `tmux` workspace model.

Includes:
- backend abstraction
- subprocess integration
- task creation and linking
- request/context handoff
- result capture

Done when:
- a routed `code_change` action launches or resumes the configured backend in the repo directory's managed `tmux` workspace
- switching between Claude Code and Codex is a config change
- completion or failure is surfaced in the conversation pane and task state

Non-goals:
- automatic post-change command generation

## Milestone 9: Adapter-backed views

Goal:
- Introduce youbot-owned adapters that render structured repo views.

Includes:
- adapter storage
- adapter loader
- command-output parsing rules
- repo-specific screens or view modes

Done when:
- an adapter can contribute repo-scoped command-palette actions
- at least one repo can display a structured view derived from command output

Non-goals:
- arbitrary plugin execution from child repos

## Milestone 10: Managed repo scaffolding

Goal:
- Initialize a new managed repo with the stricter standard.

Includes:
- scaffold generation
- required docs
- language-appropriate toolchain manifest
- baseline `justfile`

Done when:
- a new managed repo can be created from the UI or CLI
- the generated repo matches the managed repo standard in `docs/PRD.md`

## Suggested implementation discipline

- Finish milestones in order unless a later milestone is blocking a basic earlier design choice.
- Keep each milestone shippable.
- Write acceptance checks from `docs/acceptance.md` as each milestone lands.
- Avoid inventing persistence or interface shapes that contradict `docs/interfaces.md`.
