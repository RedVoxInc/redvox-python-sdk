#!/usr/bin/env bash

cd ..

if ! [[ -x "$(command -v pdoc3)" ]]; then
  echo 'Error: pdoc3 is not installed.' >&2
  exit 1
fi

set -o nounset
set -o errexit
set -o xtrace

# Remove old documentation
rm -rf docs/api_docs

# Ensure documentation directory exists
mkdir -p docs/api_docs

# Generate the API docs
pdoc3 redvox --overwrite --html --html-dir docs/api_docs -c show_type_annotations=True

# Publish to github.io

