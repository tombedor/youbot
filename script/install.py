#!/usr/bin/env python3

# assumes "poetry install" has already been run

import getpass
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess

from youbot import ROOT_DIR

memgpt_extensions_dir = os.path.join(ROOT_DIR, "youbot", "memgpt_extensions")
memgpt_install_dir = os.path.expanduser("~/.memgpt")


# flattens and symlinks python files within a dir
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

# assumes one host and one db, TODO do this with tags?
def setup_database_ssh_tunnel():
    subprocess.run("doctl auth init", shell=True, capture_output=True, text=True)
    
    
    response = subprocess.run("doctl compute droplet list --output json", shell=True, capture_output=True, text=True)
    network_infos = json.loads(response.stdout)[0]['networks']['v4']
    public_ip = next(entry['ip_address'] for entry in network_infos if entry['type'] == 'public')
    
    response = subprocess.run("doctl databases list --output json", shell=True, capture_output=True, text=True)
    db_connection_info = json.loads(response.stdout)[0]['private_connection']
    host = db_connection_info['host']
    port = db_connection_info['port']
    
    
    subprocess.run(f"ssh -N -L {port}:{host}:{port} root@{public_ip}", shell=True, capture_output=True)
    # replace background process
    # TODO: use autossh
    
    
    
    
    
    
    
    

if __name__ == "__main__":
    copy_creds()
    for name in ["functions", "personas", "humans", "presets"]:
        source_dir = os.path.join(memgpt_extensions_dir, name)
        dest_dir = os.path.join(memgpt_install_dir, name)

        symlink_files(source_dir, dest_dir)
    setup_database_ssh_tunnel()
        
    
    

    os.system("git pull origin main")
    os.system("poetry update pymemgpt")
