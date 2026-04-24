from __future__ import annotations

import asyncio
from pathlib import Path

from youbot.notifications.notifier import Notifier
from youbot.session.tmux_client import TmuxClient
from youbot.state.models import AgentSession, CodingAgent, Task

SILENCE_THRESHOLD_SECONDS = 10
MONITOR_POLL_INTERVAL = 5

PROMPT_PATTERNS: dict[CodingAgent, list[str]] = {
    CodingAgent.CLAUDE_CODE: ["> ", "? "],
    CodingAgent.CODEX: ["> ", "$ "],
}

AGENT_COMMANDS: dict[CodingAgent, str] = {
    CodingAgent.CLAUDE_CODE: "claude",
    CodingAgent.CODEX: "codex",
}


class SessionManager:
    def __init__(
        self,
        tmux: TmuxClient,
        notifier: Notifier,
    ) -> None:
        self._tmux = tmux
        self._notifier = notifier
        self._monitoring: dict[str, asyncio.Task[None]] = {}

    def start_session(
        self,
        project_name: str,
        project_path: Path,
        task: Task,
        agent: CodingAgent,
        background: bool = False,
    ) -> AgentSession:

        name = TmuxClient.session_name(project_name, task.id, agent.value)

        if not self._tmux.session_exists(name):
            session = self._tmux.create_session(name, project_path)
            session.active_window.active_pane.send_keys(AGENT_COMMANDS[agent])

        agent_session = AgentSession(
            agent=agent,
            tmux_session_name=name,
            active=True,
        )

        if background:
            loop = asyncio.get_event_loop()
            monitor_task = loop.create_task(
                self._monitor_background(project_name, task, agent_session)
            )
            self._monitoring[name] = monitor_task

        return agent_session

    def attach_session(self, agent_session: AgentSession) -> None:
        self._tmux.attach_session(agent_session.tmux_session_name)

    def is_active(self, agent_session: AgentSession) -> bool:
        return self._tmux.session_exists(agent_session.tmux_session_name)

    async def _monitor_background(
        self,
        project_name: str,
        task: Task,
        agent_session: AgentSession,
    ) -> None:
        from youbot.agents.coding_agent_supervisor import CodingAgentSupervisor

        last_content: str = ""
        silent_seconds = 0

        while self.is_active(agent_session):
            await asyncio.sleep(MONITOR_POLL_INTERVAL)
            content = self._tmux.capture_pane(agent_session.tmux_session_name)

            if content == last_content:
                silent_seconds += MONITOR_POLL_INTERVAL
            else:
                silent_seconds = 0
                last_content = content

            if silent_seconds >= SILENCE_THRESHOLD_SECONDS:
                if self._looks_like_waiting(content, agent_session.agent):
                    supervisor = CodingAgentSupervisor()
                    done = await supervisor.evaluate_and_respond(
                        project_name, task, agent_session, content
                    )
                    if done:
                        self._notifier.notify(
                            f"Task complete: {task.title}",
                            f"Background session for '{task.title}' has finished.",
                        )
                        return
                    silent_seconds = 0
                else:
                    self._notifier.notify(
                        f"Session stuck: {task.title}",
                        f"Background session for '{task.title}' appears stuck.",
                    )
                    return

    def _looks_like_waiting(self, content: str, agent: CodingAgent) -> bool:
        last_line = content.strip().splitlines()[-1] if content.strip() else ""
        return any(last_line.endswith(p) for p in PROMPT_PATTERNS.get(agent, []))
