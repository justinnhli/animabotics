#!/bin/bash

set -euo pipefail

# set python3 executable
PYTHON3=$HOME/.local/share/venv/animabotics/bin/python3
# run tests and generate coverage report if all tests passed
$PYTHON3 -m coverage run --source=animabotics -m pytest -v "$@" \
    && $PYTHON3 -m coverage html
