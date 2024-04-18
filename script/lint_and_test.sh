#!/usr/bin/env bash

set -ex

# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Change to the project root directory (assuming the script is in the scripts/ directory)
cd "$DIR/.."
ROOT_DIR=$(pwd)

# Run black formatter on the root directory
black "$ROOT_DIR"

# Run autoflake to remove unused variables and imports
find "$ROOT_DIR" -type f -name "*.py" -not -path "*/.venv/*" | xargs autoflake --remove-all-unused-imports --remove-unused-variables --in-place --exclude=__init__.py

# Run all tests
pytest "$ROOT_DIR/tests"
