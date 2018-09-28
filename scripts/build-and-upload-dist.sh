#!/usr/bin/env bash

cd ..
python3 setup.py sdist bdist_wheel

PASS=${1}
twine upload -r pypi -p ${PASS} dist/*
