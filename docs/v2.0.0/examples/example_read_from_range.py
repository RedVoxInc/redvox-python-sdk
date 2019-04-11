# import warnings
# warnings.simplefilter('error', RuntimeWarning)

import redvox.api900.summarize as summarize

if __name__ == "__main__":
    import redvox.api900.reader as reader

    # Read range and get all wrapped redvox packets in range
    grouped_packets = reader.read_rdvxz_file_range("/data/api900",
                                                   546300620,
                                                   9547305100,
                                                   ["1637060001"],
                                                   structured_layout=True,
                                                   concat_continuous_segments=True)
    # print(grouped_packets)
    print(grouped_packets["1637060001:-1103034628"][0].has_microphone_sensor.__doc__)
    summarized_data = summarize.summarize_data(grouped_packets)
    # print(summarized_data)
    summarize.plot_summarized_data(summarized_data)


