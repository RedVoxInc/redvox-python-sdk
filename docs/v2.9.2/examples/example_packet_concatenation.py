"""
This example demonstrates how to concatenate WrappedRedvoxPackets.

To follow along with this example, download example data from: https://s3-us-west-2.amazonaws.com/redvox-public/bffdf0b5-7031-4add-89f3-2eb6b9e1f1cd.zip
and place the downloaded api900 directory in the example_data directory or run the "download_example_data.sh" script.

When WrappedRedvoxPackets are concatenated, the following values are concatenated together:

* WrappedRedvoxPacket metadata
* Sensor metadata
* Sensor timestamps
* Sensor payloads

Only continuous data is concatenated. That means that gaps in the data will result in multiple WrappedRedvocPackets,
each representing a continuous segment of data.

Gaps are identified under the following circumstances:

* Greater than 5 second time gap between adjacent WrappedRedvoxPackets
* Change in microphone sampling rate
* Change in sensor name
* Change in sensor availability

Concatenation will fail under the following circumstances:

* Not all WrappedRedvoxPackets are from the same device
* WrappedRedvoxPackets are not in monotonically increasing order

Developer documentation: https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v2.9.2/redvox-api900-docs.md
API documentation: https://redvoxhi.bitbucket.io/redvox-sdk/v2.9.2/api_docs/redvox
"""

import os

# First, let's bring the reader and concat modules into scope
import redvox.api900.reader as reader
import redvox.api900.concat as concat
import redvox.api900.summarize as summarize

# Grab the absolute path to the example data
EXAMPLE_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "example_data")

# Next, let's load some data from the example data we downloaded. The example data contains an hours worth of data
# for several devices. Let's only load about 10 minutes worth of data for one device. It's worth noting that the
# read file range will concatenate the data for us automatically if we want it to. For the purpose of this example
# we disable the automatic concatenation so we can see it applied here.
grouped_packets = reader.read_rdvxz_file_range(directory=os.path.join(EXAMPLE_DATA_DIR, "api900"),
                                               start_timestamp_utc_s=1555027200,
                                               end_timestamp_utc_s=1555027800,
                                               redvox_ids=["1637160009"],
                                               structured_layout=True,
                                               concat_continuous_segments=False)

# grouped_packets is a mapping of redvox_id -> list of WrappedRedvoxPackets. Let's grab the packets for our device.
wrapped_redvox_packets = grouped_packets["1637160009:-732414658"]

# Let's see how many packets we have
print("pre-concatenate num packets", len(wrapped_redvox_packets))

# Finally, let's concatenate the packets
concatenated_packets = concat.concat_wrapped_redvox_packets(wrapped_redvox_packets)

# Let's print the new len
print("post-concatenate num packets", len(concatenated_packets))

# As you can see, the original 14 packets have been concatenated into a single packet
# Let's print out a summary of our new concatenated packet.
print(summarize.WrappedRedvoxPacketSummary(concatenated_packets[0]))
