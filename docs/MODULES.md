# Modules necesary


## Configuration / state management

### Config
global config for any app-wide configuration

### Task store
depends on: RepoRegistry (for commiting changes)

- CRUD operations on TODO.md

### Repo Registry
- tracks which apps are integrated, what their config is for auto-merge vs open pr etc
- handles commits to local .youbot repo

## Session handlers

### Tmux handler
- low level tmux operations
- opens, creates, lists tmux sessions


### SessionController
depends on: TmuxHandler for low level Tmux operations
depends on: CodingAgentSupervisor

depends on: NotificationHandler
depends on: TmuxHandler for lwo level tmux operaitons

- uses tmux `monitor-silence` with per-coding agent configuration to detect activity or idelness of background coding agents
- if background session is completed or stuck, dispatches notification, CodingAgentSupervisor for post-session tasks
- if background session needs input, dispatches CodingAgentSupervisor
- knows which sessions are active or inactive

## Agents


### Coding Agent Supervisor
depends on: TaskStore for CRUD ops on tasks

- trigger by a session going inactive, or a live coding session being exited

- provides input to coding agent for background tasks
- evaluates whether task is done for background agents
- on exit, reviews transcript, writes summary to captains log, updates task status



## NotificationHandler


## TUI views
- each view has a controller, follow standard MVC architecture. Views are under a views/ , controllers under controllers/

  - HomeView
  - ProjectDetailView
  - TaskView
  - LiveCodingSessionView
  - AddRepoView




