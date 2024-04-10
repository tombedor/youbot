#!/bin/bash
set -ex

gunicorn -c gunicorn.py function_handler:app