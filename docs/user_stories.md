# User Stories

## Purpose

This document captures the user-driven interactions that youbot must support. It complements `docs/PRD.md` by describing concrete user goals and expected product behavior, and it complements `docs/acceptance.md` by framing those behaviors from the user's perspective.

These stories should be treated as implementation-facing requirements for the TUI, routing, execution, and session model.

## Core conversational stories

### 1. Ask a repo-specific question in plain language

As a user, I want to ask a question like "what's on my to-do list?" without knowing the command name <!-- or even, possibly, the relevant repo -->, so that I can use repos through natural language.

Expected behavior:
- youbot selects the most relevant repo
- youbot runs the appropriate command or query path
- the result is shown inline in the conversation pane

### 2. Refine a previous result conversationally

As a user, I want to say things like "those openings, remote only" after a prior result, so that I can continue working without restating context.

Expected behavior:
- the follow-up uses the active repo session
- prior result context is available to routing
- the updated result replaces or follows the prior result clearly

### 3. Continue work in the same repo later

As a user, I want to come back to a repo and continue where I left off, so that ongoing work feels persistent rather than stateless.

Expected behavior:
- youbot restores the repo's prior conversation
- the last active context is visible without re-asking
- switching away and back does not lose repo-local history

### 4. Use a global conversation for cross-repo requests

As a user, I want to ask cross-repo questions without forcing a single repo context, so that I can treat youbot as an orchestrator rather than just a repo launcher.

Expected behavior:
- a global scope exists alongside repo scopes
- global requests can route across repos or ask clarifying questions
- global context is stored separately from repo-local sessions

### 5. Get a clarification instead of an incorrect action

As a user, I want youbot to ask when a request is ambiguous, so that it does not confidently do the wrong thing.

Expected behavior:
- low-confidence routing produces a clarification step
- no command is executed until ambiguity is resolved

## Navigation and scope stories

### 6. See all available repos and their state

As a user, I want to see the repos youbot knows about and whether they are usable, so that I understand what the system can act on.

Expected behavior:
- the sidebar shows registered repos
- degraded or invalid repos are clearly distinguishable
- repo status does not require leaving the main UI

### 7. Switch the active repo quickly

As a user, I want to move between repos quickly, so that I can work across several domains in one interface.

Expected behavior:
- switching repos changes active scope immediately
- the conversation pane updates to the selected repo session
- repo-specific commands update with focus

### 8. Reset a session when I want a clean slate

As a user, I want to reset a repo or global session, so that stale context does not affect new requests.

Expected behavior:
- reset is explicit and scoped
- resetting one repo does not clear other repo sessions
- resetting a repo does not destroy the global session

### 9. Branch a session when I want an alternate line of work

As a user, I want to fork a conversation into a new branch, so that I can explore an alternate direction without losing the original thread.

Expected behavior:
- branch creation is explicit
- the new branch starts with inherited context
- the original session remains available

## Command and execution stories

### 10. Discover executable capabilities through the command palette

As a user, I want to see the commands available for the current repo, so that I can use direct execution when that is faster than natural language.

Expected behavior:
- global commands are always visible
- repo-scoped commands appear only for the active repo
- command names are understandable enough to invoke intentionally

### 11. Run a known repo command directly

As a user, I want to trigger a known action directly, so that repetitive tasks are efficient.

Expected behavior:
- selecting a command runs it in the correct repo directory
- stdout, stderr, and exit status are surfaced clearly
- the result becomes part of the relevant session history

### 12. Inspect failures without losing context

As a user, I want failed commands to be visible and non-destructive, so that I can recover from errors without restarting my work.

Expected behavior:
- failures are rendered inline
- raw error output remains accessible
- the app stays usable after a command failure

## Repo onboarding and management stories

### 13. Add an existing repo with minimal friction

As a user, I want to add a repo that already exists on disk as long as it has a `justfile`, so that youbot can work with repos I do not control deeply.

Expected behavior:
- onboarding requires only a valid path and a usable `justfile`
- missing governance docs do not block integration
- initial repo metadata can live in youbot state

### 14. Supply richer metadata for a lightly documented repo

As a user, I want to add a summary, tags, and preferred commands for a repo, so that routing quality improves even when the repo itself is sparse.

Expected behavior:
- metadata is stored by youbot, not forced into the child repo
- metadata can be updated without changing the repo

### 15. Re-scan a repo after its commands change

As a user, I want youbot to refresh its command inventory, so that the UI and routing stay current when a repo evolves.

Expected behavior:
- re-scan updates command records
- stale commands are removed or marked stale
- refreshed commands appear in the palette and routing context

### 16. Initialize a new managed repo

As a user, I want youbot to scaffold a new repo when I identify a new capability area, so that new tools start from a consistent standard.

Expected behavior:
- managed repo scaffolding creates the required files and baseline commands
- the new repo is registered into youbot after creation

## Change-request stories

### 17. Request a code change when no command exists

As a user, I want to ask for a new capability in plain language, so that I do not need to manually open a repo and script the change myself.

Expected behavior:
- youbot checks for an existing command first
- if none fits, youbot routes to the code-change flow
- the result is reported back in the conversation

### 18. Promote repeated work into a first-class command

As a user, I want frequently repeated actions to become explicit commands, so that the system gets more efficient over time.

Expected behavior:
- after a successful code change, youbot can suggest or add a `just` command
- future requests can take the command path directly

## Structured view stories

### 19. See structured data in a dedicated view mode

As a user, I want results like job listings or task lists to render as structured views rather than only plain text, so that scanning and comparison are easier.

Expected behavior:
- adapters can render tables, lists, or repo-specific panels
- structured views are owned by youbot, not child repos

### 20. Apply UI-only filters to current results

As a user, I want to filter or sort visible results without necessarily re-running a command, so that exploration is fast.

Expected behavior:
- some adapter actions can operate on current displayed data
- these actions are available only when relevant to the current repo/view

## Scheduling stories

### 21. Configure recurring repo actions centrally

As a user, I want recurring tasks like nightly searches to run from youbot, so that scheduling is centralized and not duplicated inside child repos.

Expected behavior:
- schedules are configured in youbot state
- scheduled runs execute in the correct repo
- recent run results are visible in the UI

### 22. Review scheduled run outcomes

As a user, I want to inspect what happened in scheduled runs, so that background automation remains observable.

Expected behavior:
- scheduled success and failure states are persisted
- the UI exposes recent scheduled activity

## Degraded-state stories

### 23. Keep using other repos when one repo is broken

As a user, I want one missing or failing repo not to take down the whole tool, so that the orchestrator remains useful under partial failure.

Expected behavior:
- repo failures are isolated
- unaffected repos remain usable

### 24. Understand why a repo cannot be used

As a user, I want a broken repo to show a clear reason, so that I can fix the problem without guessing.

Expected behavior:
- invalid path, missing `justfile`, and command failures are surfaced distinctly

## Prioritization

The highest-priority user stories for v1 are:

1. Ask a repo-specific question in plain language
2. Continue work in the same repo later
3. Switch the active repo quickly
4. Run a known repo command directly
5. Add an existing repo with minimal friction
6. Request a code change when no command exists
7. See structured data in a dedicated view mode
8. Configure recurring repo actions centrally

## Relationship to other docs

- `docs/PRD.md` defines product scope and high-level behavior
- `docs/architecture.md` defines implementation structure
- `docs/interfaces.md` defines canonical internal records
- `docs/milestones.md` defines build order
- `docs/acceptance.md` defines testable correctness checks

If a future design choice satisfies the architecture but fails an important user story here, the user story should take precedence unless explicitly superseded.
