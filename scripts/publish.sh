#!/usr/bin/env bash

if [ -z "$1" ]
then
  echo "usage: ./publish.sh <token>"
  exit 1
fi

if ! [[ -x "$(command -v twine)" ]]; then
  echo 'Error: twine is not installed. Install from requirements_dev.txt' >&2
  exit 1
fi

TOKEN=${1}

set -o nounset
set -o errexit
set -o xtrace

cd ..
python3 -m build .

twine upload -r pypi -u __token__ -p ${TOKEN} --skip-existing dist/*

# Create a git tag for this version
VERSION="v$(python3 -c "import redvox; print(redvox.VERSION)")"
git tag -a ${VERSION} -m"Release ${VERSION}"
git push origin ${VERSION}
