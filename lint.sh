#!/bin/bash

pylint redvox.cli.cli                       && \
pylint redvox.cli.conversions               && \
pylint redvox.cli.data_req                  && \
pylint redvox.api900.concat                 && \
pylint redvox.api900.constants              && \
pylint redvox.api900.date_time_utils        && \
pylint redvox.api900.deprecation            && \
pylint redvox.api900.exceptions             && \
pylint redvox.api900.reader                 && \
pylint redvox.api900.reader_utils           && \
pylint redvox.api900.stat_utils             && \
pylint redvox.api900.summarize              && \
pylint redvox.api900.types                  && \
pylint redvox.api900.wrapped_redvox_packet  && \
pylint redvox.api900.sensors

