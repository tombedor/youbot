# Acceptance Criteria

## Purpose

This document defines observable behaviors that must hold true for the implementation to be considered correct. It is intentionally written as testable scenarios.

## Registry and discovery

- Given a configured repo path containing a `justfile`, startup registers the repo successfully.
- Given a configured repo path without a `justfile`, startup marks the repo invalid and does not expose it as ready for use.
- Given a repo with multiple `just` recipes, the parser stores each recipe as a separate command record.
- Given a previously scanned repo, rescanning updates the stored command inventory rather than duplicating it.

## Session persistence

- Given no prior state, first launch creates an empty global session.
- Given a repo message in `job_search`, switching to `life_admin` does not show that repo message in the `life_admin` conversation.
- Given prior global and repo conversations, restarting youbot restores both scopes correctly.
- Given an execution result in a repo, the result is appended to that repo's session rather than only to a global log.

## TUI shell

- The UI shows the list of registered repos and their current status.
- Selecting a repo changes the active conversation scope.
- Global actions remain available even when a repo is focused.
- The TUI starts without crashing when one configured repo is invalid.

## Command execution

- Given a discovered command, the user can invoke it from the command palette.
- A successful command shows stdout and exit code `0`.
- A failing command shows stderr and non-zero exit code without crashing the app.
- Command execution occurs in the selected repo's working directory.

## Routing

- Given a prompt clearly tied to one repo's purpose, the router selects that repo.
- Given a prompt that maps to an existing discovered command, the router returns `action_type = "command"`.
- Given an ambiguous prompt with low confidence, the system requests clarification instead of executing an arbitrary command.
- The router receives both session history and repo metadata as part of its decision context.

## Code-change flow

- Given a request not covered by an existing command, the router may return `action_type = "code_change"`.
- A code-change request launches `claude` in the target repo directory.
- A failure to launch `claude` is surfaced to the user and recorded in session history.

## Adapters and structured views

- Adapters are loaded from youbot-owned storage rather than from child repos.
- A repo can appear in the TUI without any child-repo Textual code.
- At least one adapter can transform structured command output into a non-plain-text view.
- Repo-specific command-palette entries only appear when that repo is active.

## Managed repos

- Creating a managed repo generates `PRD.md`, `AGENTS.md`, `CAPTAINS_LOG.md`, `justfile`, and `pyproject.toml`.
- The generated managed repo includes `test`, `lint`, `format`, and `install` commands in its `justfile`.
- Managed repo scaffolding follows the stricter standard even though integrated repos do not need to.

## Scheduling

- A scheduled repo command can be configured in youbot without editing the child repo.
- A scheduled run stores its result in youbot state.
- A failed scheduled run does not corrupt repo sessions or registry data.

## Failure tolerance

- A missing repo path after initial registration is shown as a degraded repo state, not a fatal startup error.
- Invalid command output is still shown as raw text when parsing fails.
- Partial failures in one repo do not prevent interaction with other repos.
