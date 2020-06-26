"""
This module shows how WrappedRedvoxPackets can be written back to disk.

Developer documentation: https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v2.9.10/redvox-api900-docs.md
API documentation: https://redvoxhi.bitbucket.io/redvox-sdk/v2.9.10/api_docs/redvox
"""

# First, we import the RedVox API 900 reader.
from redvox.api900 import reader

# Next, let's load a file to use for demonstration purposes.
wrapped_packet = reader.read_rdvxz_file("example_data/example.rdvxz")

# Let's make a small change
wrapped_packet.set_api(901)

# And now write the file back out to the current directory with the filename "example2.rdvxz"
wrapped_packet.write_rdvxz(".", "example2.rdvxz")

# Or we can serialize the data as RedVox API 900 compliant json
wrapped_packet.write_json(".", "example2.json")

# We can let the library generate a deault filename if one is not provided
wrapped_packet.write_rdvxz(".")
wrapped_packet.write_json(".")
