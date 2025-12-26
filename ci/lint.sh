#!/bin/bash

set -euo pipefail

# set python3 executable
PYTHON3=$HOME/.local/share/venv/animabotics/bin/python3
$PYTHON3 $HOME/bin/mypylint.py animabotics tests demos 2>&1 | grep -v 'no-name-in-module' | grep -v 'import-error' | sort
