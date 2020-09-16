#!/usr/bin/env bash


cd ..

VERSION=${1}

if ! [[ -x "$(command -v pdoc3)" ]]; then
  echo 'Error: pdoc3 is not installed.' >&2
  exit 1
fi

if [[ -z ${VERSION} ]]; then
    echo "missing required version"
    exit 1
fi

set -o nounset
set -o errexit
set -o xtrace


pdoc3 redvox --overwrite --html --html-dir docs/v${VERSION}/api_docs -c show_type_annotations=True
