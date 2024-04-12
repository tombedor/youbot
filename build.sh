#!/bin/bash -ue

env
mkdir -p $HOME/.memgpt/functions
pip install -r requirements.txt
python script/configure_memgpt.py