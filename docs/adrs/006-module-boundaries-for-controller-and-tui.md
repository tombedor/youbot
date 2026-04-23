# ADR 006: Package Boundaries For Controller And TUI

## Status

Accepted

## Context

The first implementation accumulated orchestration, repo-view rendering, OpenAI tool dispatch, and Textual widget rendering into a small number of large modules.

That shape made the code harder to navigate and weakened the new structural linting rules because multiple responsibilities were forced to share the same file and the same long methods.

## Decision

Youbot will keep a thin top-level orchestrator and TUI shell, while organizing related implementation into focused subpackages.

The package split is:

- `core/controller.py`
  - owns the application-facing orchestration flow
  - coordinates stores, router, executor, coding-agent runner, and OpenAI chat
- `tui/repo_view.py`
  - owns selected-repo overview rendering and overview-command presentation
- `chat/tool_handler.py`
  - owns OpenAI tool-call dispatch for repo inspection, command execution, and code-change actions
- `adapters/change.py`
  - owns construction of adapter-change prompts and the synthetic `youbot` repo target used for adapter edits
- `tui/app.py`
  - owns Textual event wiring and widget lifecycle
- `tui/layout.py`
  - owns the static Textual CSS shell
- `tui/rendering.py`
  - owns reusable render helpers for repo and activity panels
- `chat/openai_tools.py`
  - owns tool schema construction for the OpenAI Responses API
- `adapters/defaults.py`
  - owns generated default overview-section and quick-action templates
- `adapters/generation.py`
  - owns adapter inference and generated-note writing used during onboarding and refresh
- `routing/rules.py`
  - owns fallback routing heuristics, keyword tables, and argument inference
- `agents/backend.py`
  - owns backend-specific invocation construction and session-id extraction
- `agents/process.py`
  - owns subprocess launch and streamed output collection for coding-agent runs
- `agents/logs.py`
  - owns append-only run-log persistence for coding-agent executions

Supporting packages:

- `adapters/`
  - adapter loading, defaults, generation, and adapter-targeted edit prompts
- `agents/`
  - coding-agent activity, backend details, process handling, sessions, and runner orchestration
- `chat/`
  - OpenAI chat orchestration and tool schema/dispatch support
- `routing/`
  - fallback router and routing heuristics
- `state/`
  - persisted youbot-owned stores and state-derived services
- `tui/`
  - Textual shell, layout, render helpers, and repo-view rendering

## Consequences

Positive:
- Controller and TUI entry modules stay readable
- Structural linting now reinforces the intended architecture instead of being bypassed by baseline exceptions
- Repo-view rendering and tool dispatch can evolve independently

Negative:
- Behavior now spans more files, so navigation depends more on clear naming
- Small changes may sometimes require edits in both a facade module and a helper module

## Rejected alternatives

### Keep large facade modules and relax the size limits

Rejected because it would preserve the ambiguity in ownership and make the linting policy mostly symbolic.

### Split everything into many tiny files immediately

Rejected because the current codebase is still small enough that a moderate, responsibility-based split is easier to maintain than a highly granular package tree.
