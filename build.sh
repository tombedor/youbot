#!/bin/bash -ue
pwd
env
mkdir -p $HOME/.memgpt/
pip install -r requirements.txt
python script/configure_memgpt.py