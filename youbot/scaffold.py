from __future__ import annotations

from pathlib import Path

from youbot.utils import ensure_dir


MANAGED_PRD = """# PRD

Describe what this repo does and why.
"""

MANAGED_AGENTS = """# AGENTS

Document coding-agent constraints, patterns, and gotchas for this repo.
"""

MANAGED_CAPTAINS_LOG = """# CAPTAINS_LOG

## {date}

- Initial scaffold created by youbot.
"""

MANAGED_JUSTFILE = """install:
\tuv sync

format:
\truff format .

lint:
\truff check .

test:
\tpytest
"""

MANAGED_PYPROJECT = """[project]
name = "{name}"
version = "0.1.0"
description = ""
readme = "PRD.md"
requires-python = ">=3.11"

[dependency-groups]
dev = [
  "pytest",
  "ruff",
  "mypy",
]
"""


def scaffold_managed_repo(path: Path, name: str, date: str) -> None:
    ensure_dir(path)
    (path / "PRD.md").write_text(MANAGED_PRD)
    (path / "AGENTS.md").write_text(MANAGED_AGENTS)
    (path / "CAPTAINS_LOG.md").write_text(MANAGED_CAPTAINS_LOG.format(date=date))
    (path / "justfile").write_text(MANAGED_JUSTFILE)
    (path / "pyproject.toml").write_text(MANAGED_PYPROJECT.format(name=name))
