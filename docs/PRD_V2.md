# data model:
The installed youbot instance creates a local repo for it's data, and commits changes to it.

- many integrated repos
- for each repo:
    - TODO.md: Task list, if tasks were worked on, there's a branch and session id/coding agent pair. For each inactive coding session, a summary of what happened. Tasks can have one coding agent session per coding agent product per task. Ie, could have one codex session, one claude session for a given task, but not multiple codex sessions.
    - CAPTAINS_LOG.md: Session summaries, what went well, what went wrong
    - repo config: whether agent should commit to feature branch and merge without review, or whether it should just open pr. this setting is per-repo


# UI

## home:
- dashboard of projects. Default view: last session task (if any)
- if there are *background coding session* active, listed under project.

Actions available:
- select a project and enter *project detail view*
- if *background coding session* is active, can enter it

## Project detail view:
- TODO task list, with statuses.
- Lists any active *background coding session*.

Actions available:
- create a new task
- enter a *live coding session*
- create a *background coding session*
- enter a *background coding session*
- enter *task view*

## task view
- lists past sessions, with summaries

Actions available:
- enter a *live coding session*
- enter a *background coding session*
- create a *background coding session*

## live coding session
    - selecting a repo: open a tmux session
    - on exit: user goes back to dashboard
        - autoamtically in background on exit, a background agent reviews coding agent transcript, creates and persist a summary, updates TODO, updates captains log.

## Background coding session
    - runs a tmux session in the background
    - when coding agent is waiting for user response, evaluates whether task is done, and prompts for completion. Desired effect is that background coding sessions are more autonomous

## Enter background coding session
    - tmux attach into background coding session, this now becomes just like a live coding session
