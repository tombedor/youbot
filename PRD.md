# youbot

Youbot is a self-improving, multi-agent orchestrator and UI. It develops specialized capabiltiies that can then be executed and run from the CLI.

interacts with different repos that serve more specialized functions

can instantiate / delegate claude code or codex instances in different repos, to do tasks

or, execute just commands.

Different repos are integrated into youbot, their capabilities are written into justfiles, which in turn can be executed by youbot.

Youbot has a daemon that can schedule recurring tasks

# Repos

A youbot instance's capabilities are held within different repos. Some examples:
- job search repo
- kalshi trading bot
- a general life admin bot
- vector search for peresonal notes


Each repo MUST have:
- PRD.md: Description of what the repo should do
- CAPTAINS_LOG.md: Ongoing log of what changes have happened to the repo, and what task results have happened
- TODO.md: Implementation plan
- CODE_REVIEW.md: Coding guidelines
- AGENTS.md / CLAUDE.md: for coding agent instructions.
- linting / test commands

Each repo surfaces capabilities via a justfile. These can be executed either:
- via user
- via agent
- via scheduled tasks (scheduled by youbot)

## youbot repo commands
Youbot can do the following:
- execute tasks via justfiles
- execute a code review task, which analyzes the PRD, the TODO, the CODE_REVIEW, and the state of the code. It then updates the code, or documentation, as appropriate.
