#!/bin/bash -ue

env
pip install -r requirements.txt
python script/configure_memgpt.py