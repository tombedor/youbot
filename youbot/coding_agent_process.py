from __future__ import annotations

import subprocess
from threading import Thread


def launch_process(invocation: list[str], repo_path: str):
    try:
        return subprocess.Popen(
            invocation,
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
    except OSError as exc:
        return exc


def wait_for_process(
    process: subprocess.Popen[str],
    run_id: str,
    append_activity,
) -> tuple[str, str, int]:
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []
    stdout_thread = Thread(
        target=_consume_stream,
        args=(process.stdout, stdout_lines, run_id, "stdout", append_activity),
        daemon=True,
    )
    stderr_thread = Thread(
        target=_consume_stream,
        args=(process.stderr, stderr_lines, run_id, "stderr", append_activity),
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()
    return_code = process.wait()
    stdout_thread.join()
    stderr_thread.join()
    return "".join(stdout_lines), "".join(stderr_lines), return_code


def _consume_stream(
    handle,
    target: list[str],
    run_id: str,
    stream: str,
    append_activity,
) -> None:
    if handle is None:
        return
    try:
        for line in handle:
            target.append(line)
            stripped = line.rstrip()
            if stripped:
                append_activity(run_id, stream=stream, content=stripped)
    finally:
        handle.close()
