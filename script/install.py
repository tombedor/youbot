#!/usr/bin/env python3

# assumes "poetry install" has already been run

import os

# Get the current directory of the script file
script_dir = os.path.dirname(os.path.abspath(__file__))

# Change directory to the parent directory
project_base_dir = os.path.dirname(script_dir)

functions_dir = os.path.join(project_base_dir, "functions")
personas_dir = os.path.join(project_base_dir, "personas")
humans_dir = os.path.join(project_base_dir, "humans")
presets_dir = os.path.join(project_base_dir, "presets")

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
            src_file = os.path.join(root, file)
            dest_link = os.path.join(dest_dir, file)
            try:
                os.symlink(src_file, dest_dir)
                print(f"symlinked {src_file} to {dest_link}")
            except FileExistsError:
                print(f"skipped {src_file} because it already exists")


print('copying function files')
symlink_python_files(functions_dir, os.path.expanduser('~/.memgpt/functions'))
print('copying persona files')
symlink_python_files(personas_dir, os.path.expanduser('~/.memgpt/personas'))
print('copying human files')
symlink_python_files(humans_dir, os.path.expanduser('~/.memgpt/humans'))
print('copying preset files')
symlink_python_files(presets_dir, os.path.expanduser('~/.memgpt/presets'))
