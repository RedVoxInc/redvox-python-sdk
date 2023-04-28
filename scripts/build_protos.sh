#!/usr/bin/env bash

set -o nounset
set -o errexit
set -o xtrace

if ! [[ -x "$(command -v protoc)" ]]; then
  echo 'Error: protoc is not installed.' >&2
  exit 1
fi

API_900="redvox/api900/lib"
API_1000="redvox/api1000/proto"

cd ../${API_900}
protoc --python_out=. --pyi_out=. api900.proto

cd ../../../${API_1000}
protoc --python_out=. --pyi_out=. redvox_api_m.proto

# Include the sub-api version
SUB_API=$(curl https://raw.githubusercontent.com/RedVoxInc/redvox-api-1000/master/sub_api_version.txt)

TMP_FILE="/tmp/proto"
PB="redvox_api_m_pb2.py"
echo "SUB_API: float = ${SUB_API}" > ${TMP_FILE}
echo "" >> ${TMP_FILE}
cat ${PB} >> ${TMP_FILE}
cp ${TMP_FILE} ${PB}
rm ${TMP_FILE}
