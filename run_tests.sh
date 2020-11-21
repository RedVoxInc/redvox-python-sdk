#!/usr/bin/env bash

if ! [[ -x "$(command -v coverage)" ]]; then
  echo 'Error: coverage is not installed.' >&2
  exit 1
fi

set -o nounset
set -o errexit
set -o xtrace

python3 -m unittest discover
#coverage run -m unittest discover
#coverage html

# Migrations have pretty much been validated at this point. If you want to test API 900 code with migrations, you can
# uncomment the following line.
# ENABLE_MIGRATIONS="1" python3 -m unittest discover
