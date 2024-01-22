#!/usr/bin/env python3

# assumes "poetry install" has already been run

import os

# Get the current directory of the script file
script_dir = os.path.dirname(os.path.abspath(__file__))

# Change directory to the parent directory
project_base_dir = os.path.dirname(script_dir)

os.chdir(os.path.dirname(script_dir))

# Run git pull origin main
os.system("git pull origin main")
os.system("poetry update pymemgpt")

import os

# flattens and symlinks python files within a dir
def symlink_python_files(src_dir, dest_dir):
    # Ensure destination directory exists
    os.makedirs(dest_dir, exist_ok=True)

    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py') and not '.venv' in root and not 'script' in root:
                src_file = os.path.join(root, file)
                try:
                    os.symlink(src_file, dest_dir)
                    print(f"symlinked {src_file} to {dest_dir}")
                except FileExistsError:
                    print(f"skipped {src_file} because it already exists")


print('copying function files')
source_directory = os.path.expanduser('~/development/MemGPT-Functions')  # Source directory
destination_directory = os.path.expanduser('~/.memgpt/functions')  # Destination directory
symlink_python_files(source_directory, destination_directory)
