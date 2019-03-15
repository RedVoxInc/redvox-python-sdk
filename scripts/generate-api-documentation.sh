#!/usr/bin/env bash

cd ..

VERSION=${1}

if [[ -z ${VERSION} ]]; then
    echo "missing required version"
    exit 1
fi

pdoc redvox --overwrite --html --html-dir docs/${VERSION}/api_docs
