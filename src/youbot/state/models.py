from __future__ import annotations

import uuid
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    WONT_DO = "WONT_DO"


class CodingAgent(str, Enum):
    CLAUDE_CODE = "claude-code"
    CODEX = "codex"


class MergeBehavior(str, Enum):
    AUTO_MERGE = "auto-merge"
    OPEN_PR = "open-pr"


class AgentSession(BaseModel):
    agent: CodingAgent
    tmux_session_name: str
    branch: str | None = None
    active: bool = False
    summary: str | None = None


class Task(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.TODO
    sessions: list[AgentSession] = Field(default_factory=list)

    def session_for(self, agent: CodingAgent) -> AgentSession | None:
        return next((s for s in self.sessions if s.agent == agent), None)


class Project(BaseModel):
    name: str
    path: Path
    merge_behavior: MergeBehavior = MergeBehavior.OPEN_PR
