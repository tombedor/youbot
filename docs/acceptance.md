# Acceptance Criteria

## Purpose

This document defines observable behaviors that must hold true for the implementation to be considered correct. It is intentionally written as testable scenarios.

## Registry and discovery

- Given a configured repo path containing a `justfile`, startup registers the repo successfully.
- Given a configured repo path without a `justfile`, startup marks the repo invalid and does not expose it as ready for use.
- Given a repo with multiple `just` recipes, the parser stores each recipe as a separate command record.
- Given a previously scanned repo, rescanning updates the stored command inventory rather than duplicating it.
- Given a user adds a repo through the onboarding flow, the repo is persisted into config and appears in the next registry load without manual config editing.

## Conversation and coding-agent continuation

- Given no prior state, first launch creates empty youbot conversation history.
- Given prior user interactions, restarting youbot restores recent youbot conversation history.
- Given a stored coding-agent session reference for a repo, restarting youbot restores that session reference.
- Given a code-change action, the backend-native session id is stored or updated rather than reconstructing a transcript inside youbot.

## TUI shell

- The UI shows the list of registered repos and their current status.
- The UI starts in a global chat state with no repo selected by default.
- Selecting a repo changes active focus, command palette contents, and routing bias.
- Global actions remain available even when a repo is focused.
- The TUI starts without crashing when one configured repo is invalid.

## Command execution

- Given a discovered command, the user can invoke it from the command palette.
- A successful command shows stdout and exit code `0`.
- A failing command shows stderr and non-zero exit code without crashing the app.
- Command execution occurs in the selected repo's working directory.

## Routing

- Given `OPENAI_API_KEY` is configured, the primary chat path uses the OpenAI tool-calling orchestrator.
- Given a prompt clearly tied to one repo's purpose, the router selects that repo.
- Given a prompt that maps to an existing discovered command, the router returns `action_type = "command"`.
- Given an ambiguous prompt with low confidence, the system requests clarification instead of executing an arbitrary command.
- The router receives recent conversation history and repo metadata as part of its decision context.

## Code-change flow

- Given a request not covered by an existing command, the router may return `action_type = "code_change"`.
- A code-change request launches the configured coding-agent backend in the target repo directory.
- If a stored backend-native session id exists for that repo and backend, the runner uses the backend's own continuation mechanism.
- The coding-agent runner uses non-interactive backend invocation paths only.
- Switching the configured coding-agent backend from Claude Code to Codex does not require changes to calling code.
- A failure to launch the configured coding-agent backend is surfaced to the user and recorded in session history.

## Adapters and structured views

- Adapters are loaded from youbot-owned storage rather than from child repos.
- Repo onboarding generates adapter metadata in youbot-owned state.
- Repo onboarding generates selected-repo overview sections in adapter metadata when they can be inferred.
- When a repo exposes JSON-capable commands, adapters may use those structured payloads to build a more ordered workspace view.
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
- A failed scheduled run does not corrupt conversation history, coding-agent session references, or registry data.

## Failure tolerance

- A missing repo path after initial registration is shown as a degraded repo state, not a fatal startup error.
- Invalid command output is still shown as raw text when parsing fails.
- Partial failures in one repo do not prevent interaction with other repos.

## Concrete acceptance scenarios against current repos

These scenarios are intentionally tied to the current local repos so we have a real acceptance suite rather than only abstract requirements.

Reference repos:
- `../job_search`
- `../life_admin`
- `../trader-bot`

### Scenario 1: Read pipeline status from `job_search`

User interaction:
- User selects `job_search`
- User asks: "what's my current job pipeline status?"

Expected behavior:
- youbot routes to `job_search`
- youbot executes `just pipeline-status`
- command exits successfully
- output includes:
  - `## Pipeline Status`
  - the company table header
  - current pipeline entries such as `Netflix`, `Cursor`, or `Whatnot`
- the result is visible in youbot conversation history
- in the selected-repo workspace, active opportunities are shown more prominently than rejected or closed outcomes

### Scenario 2: Read current tasks from `life_admin`

User interaction:
- User selects `life_admin`
- User asks: "show me my top 5 tasks"

Expected behavior:
- youbot routes to `life_admin`
- youbot executes `just task-list 5`
- command exits successfully
- output contains task entries with a recognizable structure including:
  - task title
  - status like `[todo]`
  - `Priority:`
  - `File:`
- the output is rendered inline and visible in youbot conversation history

### Scenario 3: Keep recent conversation available while switching repos

User interaction:
1. User asks in `life_admin`: "show me my top 5 tasks"
2. User switches to `job_search`, then back to `life_admin`
3. User asks: "which of those look medium priority?"

Expected behavior:
- youbot can still use recent conversation context to interpret the follow-up
- repo focus biases the follow-up toward `life_admin`
- no irrelevant `job_search` command output is treated as the current target context

### Scenario 4: Read research program from `trader-bot`

User interaction:
- User selects `trader-bot`
- User asks: "show me the current research program"

Expected behavior:
- youbot routes to `trader-bot`
- youbot executes `just research-program`
- command exits successfully
- output contains:
  - `# Auto Research Program`
  - `## Research Goal`
  - `## Active Research Directions`
- the result is rendered inline and visible in youbot conversation history

### Scenario 5: Read research findings from `trader-bot`

User interaction:
- User selects `trader-bot`
- User asks: "what strategies has the trading bot found so far?"

Expected behavior:
- youbot routes to `trader-bot`
- youbot executes `just research-findings`
- command exits successfully
- output contains:
  - `# Research Findings`
  - at least one strategy heading such as `spotify_top10_momentum_holder`
- the result is rendered inline and visible in youbot conversation history

### Scenario 6: Surface a real command failure in `trader-bot`

User interaction:
- User selects `trader-bot`
- User asks: "list the available datasets"

Expected behavior:
- youbot routes to `trader-bot`
- youbot executes `just list-datasets`
- the current repo state may produce a non-zero exit
- if it fails, the failure is shown inline without crashing youbot
- stderr or traceback details are preserved for inspection
- the failed execution is still visible in youbot conversation history

Current observed failure signature:
- `ModuleNotFoundError: No module named 'src'`

This scenario is valuable because it tests actual failure handling against a real repo, not a synthetic fake error.

### Scenario 7: Keep repo focus and outputs distinct

User interaction:
1. User asks in `job_search`: "what's my current job pipeline status?"
2. User switches to `trader-bot` and asks: "show me the current research program"
3. User switches back to `job_search`

Expected behavior:
- repo focus and adapter state remain correct when switching back and forth
- recent conversation remains available for follow-up interpretation
- repo-specific commands and results do not get confused across focused repos

### Scenario 8: Command palette reflects active repo

User interaction:
1. User focuses `life_admin` and opens the command palette
2. User focuses `trader-bot` and opens the command palette
3. User focuses `job_search` and opens the command palette

Expected behavior:
- in `life_admin`, the palette includes commands such as:
  - `task-list`
  - `task-digest`
  - `cal-today`
- in `trader-bot`, the palette includes commands such as:
  - `research-program`
  - `research-findings`
  - `list-datasets`
- in `job_search`, the palette includes commands such as:
  - `pipeline-status`
  - `next-actions`
  - `active-openings`
- repo-specific commands do not leak across focused repos
