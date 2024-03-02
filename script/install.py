#!/usr/bin/env python3

# assumes "poetry install" has already been run

import logging
import os
import shutil

from youbot import ROOT_DIR

memgpt_extensions_dir = os.path.join(ROOT_DIR, "youbot", "memgpt_extensions")
memgpt_install_dir = os.path.expanduser("~/.memgpt")


# flattens and symlinks python files within a dir
def symlink_files(src_dir, dest_dir):
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
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
    for name in ["functions", "personas", "humans", "presets"]:
        source_dir = os.path.join(memgpt_extensions_dir, name)
        dest_dir = os.path.join(memgpt_install_dir, name)

        symlink_files(source_dir, dest_dir)

    os.system("git pull origin main")
    os.system("poetry update pymemgpt")
