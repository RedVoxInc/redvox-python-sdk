"""
This example demonstrates how to read a range of .rdvxz files from disk.

To follow along with this example, download example data from: https://s3-us-west-2.amazonaws.com/redvox-public/bffdf0b5-7031-4add-89f3-2eb6b9e1f1cd.zip
and place the downloaded api900 directory in the example_data directory or run the "download_example_data.sh" script.

Reading packets from a range always requires a time window. The packets can also be filtered by RedVox ID.

We support reading from a standardized file structure used by RedVox or reading files from an unstructured directory.

Our standardized file structure expects the following layout:
  api900/YYYY/MM/DD/*.rdvxz

Full details can be found at: https://redvoxhi.bitbucket.io/redvox-sdk/v2.0.0/api_docs/redvox/api900/reader.m.html#redvox.api900.reader.read_rdvxz_file_range

Developer documentation: https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v2.0.0/redvox-api900-docs.md
API documentation: https://redvoxhi.bitbucket.io/redvox-sdk/v2.0.0/api_docs/redvox
"""

import os

# First, let's bring in some modules
import redvox.api900.reader as reader
import redvox.api900.summarize as summarize

# Grab the absolute path to the example data
EXAMPLE_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "example_data")

# We know full data range is one hours worth of data from several devices. Let's first grab everything assuming
# that we're using a standard structured layout. This could take a couple of minutes to run as an hours worth of data
# for each device available is being concatenated.
grouped_packets = reader.read_rdvxz_file_range(os.path.join(EXAMPLE_DATA_DIR, "api900"),
                                               1555025400,  # 2019-4-11 23:30
                                               1555029000,  # 2019-4-12 00:30
                                               structured_layout=True)

# This will read all data in our structured layout, concatenating the data along the way. What we get in return is
# a dictionary mapping redvox_id -> list of concatenated packets for that device. Let's go through this dictionary and
# observe the data we loaded.
for redvox_id, concatenated_packets in grouped_packets.items():
    print(redvox_id, len(concatenated_packets))

# Just knowing the length isn't super helpful, it's also useful to summarize the data range. We can do that using the
# summarize module. This function returns a mapping from redvox id -> list of summaries for each continuous range of
# data.
summarized_data = summarize.summarize_data(grouped_packets)
for redvox_id, summaries in summarized_data.items():
    print(redvox_id, list(map(str, summaries)))

# We can also plot this summary to get a visual representation of the data. This data does now have any gaps, but
# gaps will appear as color changes or missing line for that device.
summarize.plot_summarized_data(summarized_data)

# Ok, we saw how to load all the data. Next, let's make the time window smaller and only load a subset of devices.
grouped_packets = reader.read_rdvxz_file_range(os.path.join(EXAMPLE_DATA_DIR, "api900"),
                                               1555027200,  # 2019-4-12 00:00
                                               1555027800,  # 2019-4-12 00:10
                                               redvox_ids=["1637160009", "1637681011"],
                                               structured_layout=True)

# Let's look at the summarized data
print("smaller time window, filter by redvox ids", "-" * 10)
summarized_data = summarize.summarize_data(grouped_packets)
for redvox_id, summaries in summarized_data.items():
    print(redvox_id, list(map(str, summaries)))
summarize.plot_summarized_data(summarized_data)

# We can turn off the automatic concatenation as well
grouped_packets = reader.read_rdvxz_file_range(os.path.join(EXAMPLE_DATA_DIR, "api900"),
                                               1555027200,  # 2019-4-12 00:00
                                               1555027800,  # 2019-4-12 00:10
                                               redvox_ids=["1637160009", "1637681011"],
                                               structured_layout=True,
                                               concat_continuous_segments=False)
summarized_data = summarize.summarize_data(grouped_packets)
print("disable concatenation", "-" * 10)
for redvox_id, summaries in summarized_data.items():
    print(redvox_id, list(map(str, summaries)))

# Finally, it's possible to read data from a directory that does not use our standard structured layout by passing
# False to structured_layout.

grouped_packets = reader.read_rdvxz_file_range(os.path.join(EXAMPLE_DATA_DIR, "api900", "2019", "04", "12"),
                                               1555027200,  # 2019-4-12 00:00
                                               1555027800,  # 2019-4-12 00:10
                                               redvox_ids=["1637160009", "1637681011"],
                                               structured_layout=False)
summarized_data = summarize.summarize_data(grouped_packets)
print("Read directly from directory as unstructured data", "-" * 10)
for redvox_id, summaries in summarized_data.items():
    print(redvox_id, list(map(str, summaries)))

