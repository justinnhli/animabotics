#!/bin/bash

set -euo pipefail


# set python3 executable
PYTHON3=$HOME/.local/share/venv/animabotics/bin/python3
# change to root directory
ROOT="$(realpath "$(dirname "$(realpath $0)")/..")"
cd "$ROOT"
# run all profiling benchmarks
find benchmarks -name '*.py' | while read filepath; do
    filename="$(basename "$filepath")"
    benchmark="benchmarks/${filename%.py}.benchmark"
    date="$(date '+%Y-%m-%d_%H:%M:%S')"
    revision="$(jj status | grep 'Working copy' | grep ':' | sed 's/.*: *//' | cut --delimiter=' ' --fields 1,2 | grep .)"
    output="$((time "$PYTHON3" -OO "$ROOT/benchmarks/$filename") 2>&1 | grep user | sed 's/.*\s//')"
    echo "$date $revision $output" >> "$benchmark"
done
