#!/usr/bin/env bash

cd ..
pydoc -w redvox/api900/reader.py
mv reader.html docs/reader.api.html
