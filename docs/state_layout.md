# State Layout

## Purpose

This document defines the on-disk layout for youbot-owned runtime state. It separates stable user config from mutable operational state such as sessions, discovered commands, adapter data, and execution history.

## State root

V1 should use:

```text
~/.youbot/
```

This directory is fully owned by youbot.

## Directory layout

Suggested layout:

```text
~/.youbot/
  config.json
  registry/
    repos.json
    commands.json
    routing_hints.json
  conversation/
    history.json
  coding_agent_sessions/
    sessions.json
  adapters/
    metadata/
      job_search.json
      life_admin.json
      trader-bot.json
    generated/
  scheduler/
    jobs.json
    run_history.json
  runs/
    commands.jsonl
    coding_agents.jsonl
```

This is a recommended v1 shape. The important constraint is consistency, not the exact filenames.

## Config versus state

`config.json`
- user-edited configuration
- repo registrations
- scheduler configuration
- coding-agent defaults

Everything else in the state root is mutable runtime state managed by youbot.

## Registry files

### `registry/repos.json`

Stores normalized repo metadata records.

Contents may include:
- repo id
- name
- path
- classification
- status
- purpose summary
- tags
- preferred commands
- adapter id
- timestamps

### `registry/commands.json`

Stores discovered command inventory by repo.

Contents may include:
- repo id
- command name
- display name
- description
- structured-output hints
- parse timestamps

### `registry/routing_hints.json`

Stores learned or user-supplied routing hints.

Contents may include:
- common prompt patterns
- preferred commands for common intents
- repo-specific keywords

This file is mutable and should not be treated as authoritative product logic.

## Conversation files

### `conversation/history.json`

Stores youbot's own conversation history.

This is for orchestration context and UI continuity. It is not intended to reconstruct backend-native coding-agent sessions.

## Coding-agent session registry

### `coding_agent_sessions/sessions.json`

Stores backend-native coding-agent session references by repo.

Contents may include:
- repo id
- backend name
- session kind
- session id
- purpose summary
- status
- last used timestamp

This registry stores continuation handles for automation-compatible runs, such as a Codex non-interactive session id that can later be resumed via backend-native commands like `codex exec resume <UUID>`.

## Adapter files

### `adapters/metadata/<repo_id>.json`

Stores adapter metadata and rendering hints.

Contents may include:
- adapter id
- view names
- command palette entries
- output rules
- update timestamp

### `adapters/generated/`

Reserved for generated adapter artifacts if needed later.

V1 can leave this directory empty if adapters are metadata-only.

## Scheduler files

### `scheduler/jobs.json`

Stores normalized scheduled jobs derived from config.

### `scheduler/run_history.json`

Stores recent scheduler execution outcomes.

Contents may include:
- job id
- repo id
- command name
- started/finished timestamps
- exit code
- brief summary

## Run logs

### `runs/commands.jsonl`

Append-only record of command executions.

Each line should contain:
- repo id
- command name
- invocation
- exit code
- timestamps

### `runs/coding_agents.jsonl`

Append-only record of coding-agent invocations.

Each line should contain:
- repo id
- backend name
- request summary
- exit code
- timestamps

These logs are useful for debugging and auditing, but they are not the primary source of truth for sessions.

## Data ownership rules

- Config is user-owned input.
- Registry files are youbot-owned derived state.
- Conversation files are the source of truth for youbot conversational memory.
- Coding-agent session registry is the source of truth for backend-native continuation handles.
- Adapter files are the source of truth for TUI rendering hints.
- Run logs are append-only operational history.

## Format choices

Recommended v1 formats:
- `json` for structured state snapshots
- `jsonl` for append-only event logs

Reasons:
- easy to inspect by hand
- easy to patch or recover
- no schema-migration machinery required for the first version

If the state becomes too complex later, SQLite can replace some or all of these stores behind the same interfaces.

## Recovery rules

- Missing state files should be recreated automatically.
- Corrupt per-repo state should not prevent loading other repos.
- Corrupt run logs should not block app startup.
- Config errors should be surfaced clearly because config is user-authored.
