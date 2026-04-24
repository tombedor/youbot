from __future__ import annotations

import subprocess


class Notifier:
    def notify(self, title: str, message: str) -> None:
        script = (
            f'display notification "{message}" with title "{title}"'
        )
        subprocess.run(["osascript", "-e", script], check=False)
