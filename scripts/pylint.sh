#!/bin/bash

if ! [[ -x "$(command -v pylint)" ]]; then
  echo 'Error: pylint is not installed.' >&2
  exit 1
fi

set -o nounset
#set -o errexit
set -o xtrace

cd ..

pylint redvox.api900.sensors                ##&&\
pylint redvox.api900.qa                     ##&&\
pylint redvox.api900.timesync               ##&&\

pylint redvox.api900.concat                 ##&&\
pylint redvox.api900.constants              ##&&\
pylint redvox.api900.deprecation            ##&&\
pylint redvox.api900.exceptions             ##&&\
pylint redvox.api900.location_analyzer      ##&&\
pylint redvox.api900.migrations             ##&&\
pylint redvox.api900.reader                 ##&&\
pylint redvox.api900.reader_utils           ##&&\
pylint redvox.api900.stat_utils             ##&&\
pylint redvox.api900.summarize              ##&&\
pylint redvox.api900.types                  ##&&\
pylint redvox.api900.wrapped_redvox_packet  ##&&\

pylint redvox.api1000.common                ##&&\
pylint redvox.api1000.gui                   ##&&\
pylint redvox.api1000.wrapped_redvox_packet ##&&\
pylint redvox.api1000.wrapped_redvox_packet.sensors ##&&\
pylint redvox.api1000.wrapped_redvox_packet.sensors.derived ##&&\

pylint redvox.api1000.errors ##&&\

pylint redvox.cli.cli                       ##&&\
pylint redvox.cli.conversions               ##&&\
pylint redvox.cli.data_req                  ##&&\

pylint redvox.cloud                         ##&&\

pylint redvox.common


