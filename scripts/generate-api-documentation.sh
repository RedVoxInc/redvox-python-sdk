#!/usr/bin/env bash

cd ..
source /home/redvox/venvs/redvox/bin/activate
python3 -m pydoc -w redvox/api900/reader.py
mv reader.html docs/reader.api.html
