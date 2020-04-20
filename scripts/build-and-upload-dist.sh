#!/usr/bin/env bash

set -o nounset
set -o errexit
set -o xtrace

cd ..
python3 setup.py sdist bdist_wheel

PASS=${1}
twine upload -r pypi -p ${PASS} dist/*
