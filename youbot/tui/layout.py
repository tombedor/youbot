from __future__ import annotations

APP_CSS = """
Screen {
  layout: vertical;
}

#body {
  height: 1fr;
}

#sidebar {
  width: 30;
  border: round $accent;
  background: $panel-darken-1;
  padding: 1;
  margin-right: 1;
}

#main {
  padding: 0;
}

.section-title {
  height: auto;
  padding: 0;
  text-style: bold;
  color: $text-muted;
}

#repo-shell {
  border: round green;
  background: $boost;
  padding: 0 1;
  margin-bottom: 1;
}

#repo-title {
  color: $text;
  padding-top: 1;
}

#repo-subtitle {
  height: auto;
  color: $text-muted;
  padding: 0 0 1 0;
}

#repo-view {
  height: 8;
  border: none;
  background: transparent;
  overflow: auto;
}

#chat-shell {
  height: 1fr;
  border: round blue;
  background: $surface-darken-1;
  padding: 0 1;
  margin-bottom: 1;
}

#chat-header {
  height: auto;
  padding-top: 1;
  padding-bottom: 1;
}

#conversation-title {
  color: $text;
}

#conversation {
  height: 1fr;
  border: none;
  background: transparent;
}

#activity-shell {
  height: auto;
  max-height: 14;
  border: round magenta;
  background: $surface-darken-1;
  padding: 0 1 1 1;
  margin-bottom: 1;
}

#activity-view {
  height: 1fr;
  border: none;
  background: transparent;
}

#processing-indicator {
  height: auto;
  dock: right;
  color: $text-muted;
}

#composer-shell {
  border: round yellow;
  background: $panel;
  padding: 0;
  height: auto;
  min-height: 3;
}

#input {
  border: none;
  margin: 0;
}
"""
