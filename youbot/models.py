from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


RepoClassification = Literal["integrated", "managed"]
RepoStatus = Literal["ready", "invalid", "missing", "error"]
RouteAction = Literal["command", "query", "code_change", "clarify", "global_action"]
CodingBackendName = Literal["claude_code", "codex"]
CodingSessionKind = Literal["noninteractive"]


@dataclass(slots=True)
class RepoRecord:
    repo_id: str
    name: str
    path: str
    classification: RepoClassification
    status: RepoStatus
    purpose_summary: str | None = None
    tags: list[str] = field(default_factory=list)
    preferred_commands: list[str] = field(default_factory=list)
    last_scanned_at: str | None = None
    last_active_at: str | None = None
    adapter_id: str | None = None
    preferred_backend: CodingBackendName | None = None


@dataclass(slots=True)
class CommandRecord:
    repo_id: str
    command_name: str
    display_name: str
    description: str | None
    invocation: list[str]
    supports_structured_output: bool
    structured_output_format: Literal["json", "text", "unknown"]
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ConversationMessage:
    message_id: str
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    created_at: str


@dataclass(slots=True)
class ConversationRecord:
    conversation_id: str
    messages: list[ConversationMessage]
    updated_at: str
    last_response_id: str | None = None


@dataclass(slots=True)
class RouteDecision:
    repo_id: str | None
    action_type: RouteAction
    command_name: str | None
    arguments: list[str]
    reasoning_summary: str
    confidence: float


@dataclass(slots=True)
class CodingAgentBackend:
    backend_name: CodingBackendName
    command_prefix: list[str]
    default_args: list[str]


@dataclass(slots=True)
class ExecutionResult:
    repo_id: str
    command_name: str
    invocation: list[str]
    exit_code: int
    stdout: str
    stderr: str
    started_at: str
    finished_at: str
    duration_ms: int
    parsed_payload: dict | list | None = None


@dataclass(slots=True)
class CodingAgentResult:
    repo_id: str
    backend_name: CodingBackendName
    exit_code: int
    stdout: str
    stderr: str
    started_at: str
    finished_at: str
    duration_ms: int
    session_id: str | None = None


@dataclass(slots=True)
class CodingAgentSessionRef:
    repo_id: str
    backend_name: CodingBackendName
    session_kind: CodingSessionKind
    session_id: str
    purpose_summary: str | None
    status: Literal["active", "stale", "unknown"]
    last_used_at: str


@dataclass(slots=True)
class OverviewSectionSpec:
    command_name: str
    arguments: list[str] = field(default_factory=list)
    title: str | None = None
    max_lines: int = 14
    fallback_command_names: list[str] = field(default_factory=list)
    render_mode: Literal["json", "text"] = "text"


@dataclass(slots=True)
class QuickActionSpec:
    command_name: str
    title: str | None = None
    arguments: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AdapterRecord:
    adapter_id: str
    repo_id: str
    version: str
    view_names: list[str]
    command_palette_entries: list[str]
    output_rules: list[str]
    updated_at: str
    overview_sections: list[OverviewSectionSpec] = field(default_factory=list)
    quick_actions: list[QuickActionSpec] = field(default_factory=list)
