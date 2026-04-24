from __future__ import annotations

import anthropic

from youbot.state.models import AgentSession, Task, TaskStatus
from youbot.state.task_repository import TaskRepository

_EVALUATE_PROMPT = """\
You are supervising a background coding session. Below is the current terminal output.

Task: {title}
Description: {description}

Terminal output:
{content}

Is the task complete? If yes, respond with DONE.
If the agent needs a nudge to continue or wrap up, respond with the message to send it."""


class CodingAgentSupervisor:
    def __init__(self) -> None:
        self._client = anthropic.Anthropic()

    async def evaluate_and_respond(
        self,
        project_name: str,
        task: Task,
        agent_session: AgentSession,
        pane_content: str,
    ) -> bool:
        from youbot.session.tmux_client import TmuxClient

        prompt = _EVALUATE_PROMPT.format(
            title=task.title,
            description=task.description or "No description",
            content=pane_content[-3000:],
        )

        message = self._client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        response = message.content[0].text.strip()

        if response.upper() == "DONE":
            return True

        tmux = TmuxClient()
        tmux.send_keys(agent_session.tmux_session_name, response)
        return False

    def run_post_mortem(
        self,
        project_name: str,
        task: Task,
        agent_session: AgentSession,
        pane_content: str,
        task_repo: TaskRepository,
    ) -> None:
        prompt = f"""\
A coding session just ended. Review the terminal output and:
1. Write a short summary (2-4 sentences) of what happened.
2. Decide the task status: COMPLETE, IN_PROGRESS, TODO, or WONT_DO.

Task: {task.title}
Description: {task.description or "No description"}

Terminal output:
{pane_content[-4000:]}

Respond in this exact format:
STATUS: <status>
SUMMARY: <summary>"""

        message = self._client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        response = message.content[0].text.strip()

        lines = response.splitlines()
        status_line = next((ln for ln in lines if ln.startswith("STATUS:")), None)
        summary_line = next((ln for ln in lines if ln.startswith("SUMMARY:")), None)

        if status_line:
            try:
                task.status = TaskStatus(status_line.split(":", 1)[1].strip())
            except ValueError:
                pass

        if summary_line:
            agent_session.summary = summary_line.split(":", 1)[1].strip()

        agent_session.active = False
        task_repo.update(task)
        self._append_captains_log(project_name, task, agent_session)

    def _append_captains_log(
        self,
        project_name: str,
        task: Task,
        agent_session: AgentSession,
    ) -> None:
        from datetime import date

        from youbot.state.project_registry import project_dir

        log_file = project_dir(project_name) / "CAPTAINS_LOG.md"
        entry = (
            f"\n## {date.today()} — {task.title} [{agent_session.agent.value}]\n\n"
            f"{agent_session.summary or 'No summary.'}\n"
        )
        with log_file.open("a") as f:
            f.write(entry)
