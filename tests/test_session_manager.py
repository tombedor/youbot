from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import Mock

from youbot.notifications.notifier import Notifier
from youbot.session.session_manager import SessionManager
from youbot.session.tmux_client import TmuxClient


def test_capture_pane_joins_lines() -> None:
    pane = SimpleNamespace(capture_pane=Mock(return_value=["line 1", "line 2", "$ "]))
    session = SimpleNamespace(active_window=SimpleNamespace(active_pane=pane))
    client = TmuxClient()
    client.get_session = Mock(return_value=session)  # type: ignore[method-assign]

    assert client.capture_pane("demo") == "line 1\nline 2\n$ "


def test_monitor_done_notifies_on_failure() -> None:
    notifier = Mock(spec=Notifier)
    manager = SessionManager(tmux=Mock(), notifier=notifier)
    task = asyncio.Future()
    task.set_exception(RuntimeError("boom"))
    manager._monitoring["demo"] = task  # type: ignore[assignment]

    manager._on_monitor_done("demo", task)  # type: ignore[arg-type]

    assert "demo" not in manager._monitoring
    notifier.notify.assert_called_once_with(
        "Background session failed",
        "Monitoring failed for tmux session 'demo'.",
    )
