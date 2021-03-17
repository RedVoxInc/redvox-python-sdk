#!/usr/bin/env bash

if ! [[ -x "$(command -v coverage)" ]]; then
  echo 'Error: coverage is not installed.' >&2
  exit 1
fi

set -o nounset
set -o errexit
set -o xtrace

cd ..

python3 -m unittest discover
