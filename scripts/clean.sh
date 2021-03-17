#!/usr/bin/env bash

set -o nounset
set -o errexit
set -o xtrace

cd ..
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
rm -rf build
rm -rf dist
rm -rf redvox.egg-info
rm -rf htmlcov
rm -rf .coverage
rm -rf .mypy_cache
