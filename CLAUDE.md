# Claude Code Instructions

## Source of truth

Treat the docs in `docs/` as the source of truth for intended behavior.

If you change how youbot behaves, update the docs in the same change. Do not rely on implementation drift becoming the de facto spec.

## Which docs to update

Update the relevant files based on the type of change:

- `docs/PRD.md`: product behavior, interaction model, repo integration model, adapter model
- `docs/architecture.md`: control flow, module responsibilities, onboarding flow, runtime flow
- `docs/interfaces.md`: data models, service interfaces, ownership boundaries
- `docs/user_stories.md`: user-visible workflows and stories
- `docs/acceptance.md`: testable expected behavior and concrete scenarios
- `docs/state_layout.md`: `~/.youbot/` files and state ownership
- `docs/config.md`: config fields, env vars, defaults, config boundaries
- `docs/milestones.md`: implementation sequencing and milestone definitions
- `docs/adrs/*.md`: durable architectural decisions

## Expected development flow

1. Read the relevant docs first.
2. Implement the code change.
3. Update the docs so they describe the new truth.
4. Run focused verification.
5. Commit code and docs together when possible.

## Onboarding and adapter generation

Repo onboarding should include:
- repo validation
- command discovery from `justfile`
- generation of adapter metadata in youbot-owned state
- generation of any adapter artifacts needed for the selected-repo workspace

Do not push Textual-specific adapter code into child repos.

## Practical rule

If you touch:
- control flow
- persisted state
- adapter behavior
- onboarding behavior
- user-visible UI behavior

then you should assume at least one doc in `docs/` must also change.
