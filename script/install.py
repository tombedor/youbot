#!/usr/bin/env python3

# assumes "poetry install" has already been run

import logging
import os

from youbot import ROOT_DIR

memgpt_extensions_dir = os.path.join(ROOT_DIR, "youbot", "memgpt_extensions")
memgpt_install_dir = os.path.expanduser("~/.memgpt")


# flattens and symlinks python files within a dir
def symlink_files(src_dir, dest_dir):
    logging.info(f"symlinking files from {src_dir} to {dest_dir}")
    # Ensure destination directory exists
    os.makedirs(dest_dir, exist_ok=True)

    for root, dirs, files in os.walk(src_dir):
        for file in files:
            src_file = os.path.join(root, file)
            dest_path = os.path.join(dest_dir, file)

            # if dest exists, rm it
            if os.path.exists(dest_path):
                os.remove(dest_path)
            os.symlink(src_file, dest_path)
            print(f"symlinked {src_file} to {dest_path}")


if __name__ == "__main__":
    for name in ["functions", "personas", "humans", "presets"]:
        source_dir = os.path.join(memgpt_extensions_dir, name)
        dest_dir = os.path.join(memgpt_install_dir, name)

        symlink_files(source_dir, dest_dir)

    os.system("git pull origin main")
    os.system("poetry update pymemgpt")
