from __future__ import annotations

import re
from pathlib import Path

from youbot.models import CommandRecord, RepoRecord

RECIPE_RE = re.compile(r"^([A-Za-z0-9_-]+)(?:\s+[^:]*)?\s*:\s*$")


class JustfileParser:
    def parse_repo(self, repo: RepoRecord) -> list[CommandRecord]:
        justfile = Path(repo.path) / "justfile"
        if not justfile.exists():
            return []

        commands: list[CommandRecord] = []
        pending_comment: str | None = None
        for line in justfile.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                comment = stripped.removeprefix("#").strip()
                pending_comment = comment or pending_comment
                continue
            if not stripped or line.startswith((" ", "\t")):
                continue
            if ":=" in line:
                pending_comment = None
                continue
            match = RECIPE_RE.match(line)
            if match is None:
                pending_comment = None
                continue
            command_name = match.group(1)
            description = pending_comment
            commands.append(
                CommandRecord(
                    repo_id=repo.repo_id,
                    command_name=command_name,
                    display_name=command_name,
                    description=description,
                    invocation=["just", command_name],
                    supports_structured_output=False,
                    structured_output_format="unknown",
                    tags=[],
                )
            )
            pending_comment = None
        return commands
