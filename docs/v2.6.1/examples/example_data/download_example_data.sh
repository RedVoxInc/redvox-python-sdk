#!/usr/bin/env bash

DATA_SET="bffdf0b5-7031-4add-89f3-2eb6b9e1f1cd.zip"
curl https://s3-us-west-2.amazonaws.com/redvox-public/${DATA_SET} -O
unzip ${DATA_SET}
rm ${DATA_SET}