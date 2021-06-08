#!/usr/bin/env bash

if ! [[ -x "$(command -v markdown-toc)" ]]; then
  echo 'Error: markdown-toc is not installed. See: https://github.com/jonschlinkert/markdown-toc' >&2
  exit 1
fi

set -o nounset
set -o errexit
set -o xtrace

markdown-toc -i installation.md
markdown-toc -i low_level_api.md
markdown-toc -i cli/README.md
markdown-toc -i cloud/README.md
markdown-toc -i data_window/README.md
markdown-toc -i data_window/station/README.md
