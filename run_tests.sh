#!/usr/bin/env bash

if ! [[ -x "$(command -v coverage)" ]]; then
  echo 'Error: coverage is not installed.' >&2
  exit 1
fi

coverage run -m unittest discover
coverage html
