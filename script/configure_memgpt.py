#!/usr/bin/env python3

import os
from pathlib import Path

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

memgpt_extensions_dir = os.path.join(root_dir, "youbot", "memgpt_extensions")
memgpt_install_dir = os.path.expanduser("~/.memgpt")


def symlink_files(src_dir, dest_dir):
    if os.path.exists(dest_dir):
        path = Path(dest_dir)
        path.unlink()
    os.symlink(src_dir, dest_dir)


def copy_creds():
    openai_key = os.environ["OPENAI_API_KEY"]
    creds_text = f"""
[openai]
auth_type = bearer_token
key = {openai_key}
"""

    creds_path = os.path.join(os.path.expanduser("~"), ".memgpt", "credentials")
    with open(creds_path, "w") as file:
        file.write(creds_text)


if __name__ == "__main__":
    copy_creds()
    for name in ["functions"]:
        source_dir = os.path.join(memgpt_extensions_dir, name)
        dest_dir = os.path.join(memgpt_install_dir, name)
        symlink_files(source_dir, dest_dir)
