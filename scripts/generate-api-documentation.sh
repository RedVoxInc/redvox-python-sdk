#!/usr/bin/env bash

cd ..
python3 -m pydoc -w redvox/api900/reader.py
mv reader.html reader.api.html
