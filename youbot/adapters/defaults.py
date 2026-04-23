from __future__ import annotations

from youbot.core.models import OverviewSectionSpec, QuickActionSpec

PREFERRED_OVERVIEW_SECTIONS: dict[str, list[OverviewSectionSpec]] = {
    "job_search": [
        OverviewSectionSpec(
            command_name="pipeline-status",
            arguments=["json"],
            title="Active Pipeline",
            render_mode="json",
            max_lines=12,
            fallback_command_names=["active-openings"],
        ),
        OverviewSectionSpec(
            command_name="next-actions",
            arguments=["json"],
            title="Next Actions",
            render_mode="json",
            max_lines=8,
        ),
        OverviewSectionSpec(
            command_name="active-openings",
            arguments=["json"],
            title="Top Openings",
            render_mode="json",
            max_lines=6,
        ),
    ],
    "life_admin": [
        OverviewSectionSpec(
            command_name="task-digest",
            arguments=["json"],
            title="Priority Digest",
            render_mode="json",
            max_lines=10,
            fallback_command_names=["task-list"],
        ),
        OverviewSectionSpec(
            command_name="task-list",
            arguments=["5", "json"],
            title="Top Tasks",
            render_mode="json",
            max_lines=8,
        ),
    ],
    "trader-bot": [
        OverviewSectionSpec(
            command_name="research-program",
            title="Research Program",
            render_mode="text",
            max_lines=14,
            fallback_command_names=["research-findings"],
        ),
        OverviewSectionSpec(
            command_name="research-findings",
            title="Recent Findings",
            render_mode="text",
            max_lines=14,
        ),
    ],
}

PREFERRED_QUICK_ACTIONS: dict[str, list[QuickActionSpec]] = {
    "job_search": [
        QuickActionSpec(command_name="pipeline-status", title="Pipeline"),
        QuickActionSpec(command_name="next-actions", title="Next actions"),
        QuickActionSpec(command_name="active-openings", title="Openings"),
        QuickActionSpec(command_name="action-items", title="Action items"),
    ],
    "life_admin": [
        QuickActionSpec(command_name="task-digest", title="Priority digest"),
        QuickActionSpec(command_name="task-list", title="Top tasks", arguments=["5"]),
        QuickActionSpec(command_name="task-create", title="Add task"),
        QuickActionSpec(command_name="task-search", title="Search tasks"),
    ],
    "trader-bot": [
        QuickActionSpec(command_name="research-program", title="Research program"),
        QuickActionSpec(command_name="research-findings", title="Recent findings"),
        QuickActionSpec(command_name="research-cycle", title="Run research"),
        QuickActionSpec(command_name="list-markets", title="List markets"),
    ],
}
