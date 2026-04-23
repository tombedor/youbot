from __future__ import annotations

import re

from youbot.models import CodingAgentBackend, CodingAgentSessionRef
from youbot.utils import make_id

CODEX_SESSION_RE = re.compile(r"session id:\s*([0-9a-fA-F-]{36})")


def build_invocation(
    backend: CodingAgentBackend,
    session_ref: CodingAgentSessionRef | None,
    request: str,
    context: str | None,
) -> tuple[list[str], str | None]:
    prompt = request if context is None else f"{context}\n\n{request}"
    if backend.backend_name == "codex":
        return _build_codex_invocation(backend, session_ref, prompt)
    return _build_claude_invocation(backend, session_ref, prompt)


def extract_session_id(
    backend_name: str,
    output: str,
    session_ref: CodingAgentSessionRef | None,
    seeded_session_id: str | None,
) -> str | None:
    if backend_name == "codex":
        match = CODEX_SESSION_RE.search(output)
        if match is not None:
            return match.group(1)
        return None if session_ref is None else session_ref.session_id
    if backend_name == "claude_code":
        return seeded_session_id or (None if session_ref is None else session_ref.session_id)
    return None if session_ref is None else session_ref.session_id


def _build_codex_invocation(
    backend: CodingAgentBackend,
    session_ref: CodingAgentSessionRef | None,
    prompt: str,
) -> tuple[list[str], str | None]:
    if session_ref is not None and session_ref.backend_name == "codex":
        return [
            *backend.command_prefix,
            *backend.default_args,
            "exec",
            "resume",
            session_ref.session_id,
            prompt,
        ], session_ref.session_id
    return [*backend.command_prefix, *backend.default_args, "exec", prompt], None


def _build_claude_invocation(
    backend: CodingAgentBackend,
    session_ref: CodingAgentSessionRef | None,
    prompt: str,
) -> tuple[list[str], str | None]:
    if session_ref is not None and session_ref.backend_name == "claude_code":
        return [
            *backend.command_prefix,
            *backend.default_args,
            "-p",
            "--resume",
            session_ref.session_id,
            prompt,
        ], session_ref.session_id
    session_id = make_id()
    return [
        *backend.command_prefix,
        *backend.default_args,
        "-p",
        "--session-id",
        session_id,
        prompt,
    ], session_id
