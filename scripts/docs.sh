#!/usr/bin/env bash

if ! [[ -x "$(command -v pdoc3)" ]]; then
  echo 'Error: pdoc3 is not installed.' >&2
  exit 1
fi

set -o nounset
set -o errexit
set -o xtrace

# Ensure RedVox configuration isn't brought into API documentation
./check_user_config.py

cd ..

# Remove old documentation
rm -rf docs/api_docs

# Ensure documentation directory exists
mkdir -p docs/api_docs

# Generate the API docs
pdoc3 redvox --overwrite --html --html-dir docs/api_docs -c show_type_annotations=True

# Publish to github.io
TMP_DIR="/tmp/redvox_docs"
rm -rf ${TMP_DIR}
mkdir -p ${TMP_DIR}
git clone git@github.com:RedVoxInc/RedVoxInc.github.io.git ${TMP_DIR}
rm -rf ${TMP_DIR}/redvox-sdk/api_docs
cp -r docs/api_docs ${TMP_DIR}/redvox-sdk
cd ${TMP_DIR}
git add -A
git commit -m"Update RedVox Python SDK API Docs"
git push origin master

