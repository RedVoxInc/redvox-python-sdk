"""
This example demonstrates how to read a range of .rdvxz files from disk.

To follow along with this example, download example data from: https://s3-us-west-2.amazonaws.com/redvox-public/bffdf0b5-7031-4add-89f3-2eb6b9e1f1cd.zip
and place the downloaded api900 directory in the example_data directory or run the "download_example_data.sh" script.

Reading packets from a range always requires a time window. The packets can also be filtered by RedVox ID.



Developer documentation: https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v2.0.0/redvox-api900-docs.md
API documentation: https://redvoxhi.bitbucket.io/redvox-sdk/v2.0.0/api_docs/redvox
"""

import os

# First, let's bring the reader and concat modules into scope
import redvox.api900.concat as concat
import redvox.api900.reader as reader
import redvox.api900.summarize as summarize

# Grab the absolute path to the example data
EXAMPLE_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "example_data")