#!/usr/bin/env bash

if ! [[ -x "$(command -v coverage)" ]]; then
  echo 'Error: coverage is not installed.' >&2
  exit 1
fi

coverage run -m unittest discover
coverage html

# Run the tests again with API 1000 migrations turned on
ENABLE_MIGRATIONS="1" python3 -m unittest discover
