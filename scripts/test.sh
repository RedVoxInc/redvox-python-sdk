#!/usr/bin/env bash

set -o nounset
set -o errexit
set -o xtrace

cd ..

python3 -m unittest discover
