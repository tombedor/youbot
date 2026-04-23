from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from rich.panel import Panel

from youbot import cli, config
from youbot.agents.activity import CodingAgentActivityStore
from youbot.core.controller import AppController
from youbot.core.models import (
    CodingAgentActivityEntry,
    CodingAgentActivitySnapshot,
    CodingAgentResult,
    ConversationRecord,
    RepoRecord,
)
from youbot.routing.router import Router
from youbot.state.usage_review import UsageReviewService
from youbot.utils import ensure_dir


def _write_usage_review_fixtures(tmp_path: Path) -> None:
    ensure_dir(tmp_path / "conversation")
    ensure_dir(tmp_path / "runs")
    ensure_dir(tmp_path / "activity")
    ts0 = "2026-01-01T00:00:00Z"
    ts1 = "2026-01-01T00:00:01Z"
    (tmp_path / "conversation" / "history.json").write_text(
        json.dumps(
            {
                "conversation_id": "conv-1",
                "messages": [
                    {"message_id": "m1", "role": "user", "content": "hello", "created_at": ts0},
                    {"message_id": "m2", "role": "assistant", "content": "hi", "created_at": ts1},
                ],
                "updated_at": ts1,
                "last_response_id": "resp_123",
            }
        )
    )
    (tmp_path / "runs" / "commands.jsonl").write_text(
        json.dumps({"repo_id": "life_admin", "command_name": "task-list", "exit_code": 0}) + "\n"
    )
    (tmp_path / "runs" / "coding_agents.jsonl").write_text(
        json.dumps(
            {
                "repo_id": "youbot",
                "backend_name": "codex",
                "target_kind": "adapter",
                "exit_code": 0,
            }
        )
        + "\n"
    )
    (tmp_path / "activity" / "coding_agent_events.jsonl").write_text(
        json.dumps(
            {
                "run_id": "run-1",
                "event": "started",
                "stream": "status",
                "content": "Starting codex session.",
            }
        )
        + "\n"
    )
    (tmp_path / "activity" / "coding_agent_current.json").write_text(
        json.dumps(
            {
                "run_id": "run-1",
                "status": "running",
                "repo_id": "youbot",
                "backend_name": "codex",
                "target_kind": "adapter",
                "request_summary": "update adapter",
                "session_id": None,
                "started_at": ts0,
                "updated_at": ts1,
                "entries": [],
            }
        )
    )


def test_usage_review_builds_bundle_from_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(config, "DEFAULT_STATE_ROOT", tmp_path)
    _write_usage_review_fixtures(tmp_path)

    service = UsageReviewService()
    bundle, bundle_path = service.build_and_write_bundle()

    assert bundle.conversation_id == "conv-1"
    assert len(bundle.messages) == 2
    assert bundle.command_runs[0]["command_name"] == "task-list"
    assert bundle.coding_agent_runs[0]["target_kind"] == "adapter"
    assert bundle.activity_entries[0]["event"] == "started"
    assert bundle.activity_log_refs
    assert bundle_path.exists()


def test_router_prefers_adapter_change_for_view_requests() -> None:
    router = Router()
    repos = [
        RepoRecord(
            repo_id="life_admin",
            name="life_admin",
            path="/tmp/life_admin",
            classification="integrated",
            status="ready",
        )
    ]

    decision = router.route(
        "change the life_admin view to show overdue tasks first",
        "life_admin",
        conversation=ConversationRecord(
            conversation_id="conv-1",
            messages=[],
            updated_at="2026-01-01T00:00:00Z",
        ),
        repos=repos,
        commands={"life_admin": []},
    )

    assert decision.action_type == "adapter_change"
    assert decision.repo_id == "life_admin"


def test_activity_store_records_lifecycle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "DEFAULT_STATE_ROOT", tmp_path)
    store = CodingAgentActivityStore()

    snapshot = store.start(
        run_id="run-1",
        repo_id="youbot",
        backend_name="codex",
        target_kind="adapter",
        request_summary="tweak life_admin view",
    )
    assert snapshot.status == "running"

    store.append("run-1", stream="status", content="Starting codex session.")
    store.append("run-1", stream="stdout", content="session id: 123")
    store.set_session_id("run-1", "123")
    finished = store.finish("run-1", exit_code=0, session_id="123")

    assert finished is not None
    assert finished.status == "finished"
    assert finished.session_id == "123"
    assert finished.exit_code == 0
    assert len(finished.entries) == 2
    assert store.get_current() is not None


def test_controller_builtin_review_usage_records_assistant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(config, "DEFAULT_STATE_ROOT", tmp_path)
    controller = AppController()

    processed = controller.process_message("/review-usage", None)

    assert processed.summary == "Usage review"
    assert "Generated a usage review bundle" in processed.body
    conversation = controller.conversation_store.get_conversation()
    assert conversation.messages[-1].role == "assistant"


def test_controller_run_adapter_change_targets_youbot_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(config, "DEFAULT_STATE_ROOT", tmp_path)
    controller = AppController()
    captured: dict[str, object] = {}

    def fake_run_code_change(
        repo: RepoRecord,
        request: str,
        context: str | None = None,
        *,
        target_kind: str = "repo",
    ) -> CodingAgentResult:
        _ = context
        captured["repo"] = repo
        captured["request"] = request
        captured["target_kind"] = target_kind
        return CodingAgentResult(
            repo_id=repo.repo_id,
            backend_name="codex",
            target_kind="adapter",
            exit_code=0,
            stdout="ok",
            stderr="",
            started_at="2026-01-01T00:00:00Z",
            finished_at="2026-01-01T00:00:01Z",
            duration_ms=1,
            session_id="session-1",
        )

    controller.coding_agent_runner.run_code_change = fake_run_code_change  # type: ignore[method-assign]
    target_repo = RepoRecord(
        repo_id="life_admin",
        name="life_admin",
        path="/tmp/life_admin",
        classification="integrated",
        status="ready",
    )

    body = controller.run_adapter_change(
        target_repo,
        "change the life_admin view to show overdue tasks first",
    )

    run_repo = captured["repo"]
    assert isinstance(run_repo, RepoRecord)
    assert run_repo.repo_id == "youbot"
    assert captured["target_kind"] == "adapter"
    assert "Do not edit the child repo" in str(captured["request"])
    assert "Target integrated repo: life_admin" in str(captured["request"])
    assert "Target: adapter" in body


def test_cli_review_usage_outputs_bundle_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(config, "DEFAULT_STATE_ROOT", tmp_path)

    class FakeController:
        def review_usage(self) -> tuple[str, str]:
            return "reviewed recent usage", "/tmp/bundle.json"

    monkeypatch.setattr(cli, "AppController", FakeController)
    monkeypatch.setattr(sys, "argv", ["youbot", "review-usage"])

    cli.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"] == "reviewed recent usage"
    assert payload["bundle_path"] == "/tmp/bundle.json"


def test_activity_panel_formatter_includes_recent_entries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from youbot.tui import app as app_module

    class FakeController:
        def get_coding_agent_activity(self) -> None:
            return None

    monkeypatch.setattr(app_module, "AppController", FakeController)
    youbot_app = app_module.YoubotApp()
    snapshot = CodingAgentActivitySnapshot(
        run_id="run-1",
        status="running",
        repo_id="youbot",
        backend_name="codex",
        target_kind="adapter",
        request_summary="update life_admin adapter",
        session_id="session-1",
        started_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:02Z",
        entries=[
            CodingAgentActivityEntry(
                stream="status",
                content="Starting codex session.",
                created_at="2026-01-01T00:00:00Z",
            ),
            CodingAgentActivityEntry(
                stream="stdout",
                content="Applied adapter update.",
                created_at="2026-01-01T00:00:01Z",
            ),
        ],
    )

    panel = youbot_app._build_activity_panel(snapshot)

    assert isinstance(panel, Panel)
    assert "Coding Activity: update life_admin adapter" in str(panel.title)
    assert "[status] Starting codex session." in str(panel.renderable)
    assert "[out] Applied adapter update." in str(panel.renderable)
