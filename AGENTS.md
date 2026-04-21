# Agent Instructions

## Purpose

This repo treats documentation as the source of truth for what youbot is supposed to do.

If implementation and docs disagree, do not silently optimize around the code. Either:
- update the code to match the docs, or
- update the docs in the same change if the intended behavior has changed

Do not leave the repo in a state where product behavior has changed but the docs still describe the old system.

## Required doc updates

When changing product behavior, architecture, workflows, or persisted state, update the relevant docs in the same change.

Use this mapping:

- `docs/PRD.md`
  Update when product scope, interaction model, repo integration model, adapter model, or core user-facing behavior changes.

- `docs/architecture.md`
  Update when control flow, module responsibilities, onboarding flow, runtime flow, or persistence responsibilities change.

- `docs/interfaces.md`
  Update when dataclasses, persisted record shapes, service interfaces, or ownership boundaries change.

- `docs/user_stories.md`
  Update when new user-visible flows are added, removed, or materially changed.

- `docs/acceptance.md`
  Update when acceptance behavior changes, when new concrete scenarios are added, or when implementation now covers a previously missing case.

- `docs/state_layout.md`
  Update when files under `~/.youbot/` change shape, ownership, or meaning.

- `docs/config.md`
  Update when config fields, environment variables, defaults, or configuration boundaries change.

- `docs/milestones.md`
  Update when implementation sequencing or milestone definitions materially change.

- `docs/adrs/*.md`
  Add or update an ADR when a durable architectural decision is made or reversed.

## Development flow

For non-trivial work, follow this order:

1. Read the relevant docs before changing code.
2. Make the implementation change.
3. Update the docs that describe the changed behavior.
4. Run focused verification.
5. Check that docs and implementation still agree before committing.

## Expectations for repo onboarding and adapters

Repo onboarding is not just command discovery.

When onboarding or refreshing a repo, you should treat adapter generation as part of the flow:
- discover commands from the repo's `justfile`
- generate adapter metadata in youbot-owned state
- generate any adapter artifacts needed for the selected-repo workspace
- keep adapter definitions out of the child repo

If adapter behavior changes, update both implementation and the docs that describe onboarding and adapter responsibilities.

## Commit discipline

Prefer commits that keep code and docs synchronized.

If a change introduces:
- a new runtime path
- a new persisted field
- a new onboarding step
- a new user-visible interaction

then the same commit should usually include the corresponding doc updates.
