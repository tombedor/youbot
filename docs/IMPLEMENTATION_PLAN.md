# Modules necesary


## Configuration / state management

### ConfigHandler
- reads config values
- makes changes to config values

## Task store
- CRUD operations on TODO.md

## Repo Registry
tracks which apps are integrated, what their config is for auto-merge vs open pr etc


## Tmux handler
- opens, creates, lists tmux sessions

## Coding agent session handler
- interfaces with tmux handler
- knows which sessions are active or inactive

## Background session monitor
- watches background tmux panes for coding agents waiting for input

## Post session agent
- trigger on session exit
- for background sessions, evaluates whether task is done, responds to coding agent

## TUI views
- fiels for various views

## Notifications


