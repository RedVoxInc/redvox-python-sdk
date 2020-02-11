from typing import Dict, List

import numpy as np

import redvox.api900.reader as reader


def main():
    device_to_packets: Dict[str, List[reader.WrappedRedvoxPacket]] = reader.read_rdvxz_file_range(
        "/Users/anthony/scrap/api900",
        concat_continuous_segments=False,
        structured_layout=True)
    data: List[reader.WrappedRedvoxPacket] = device_to_packets["1637610012:1608801060"]
    timestamps: List[int] = list(map(reader.WrappedRedvoxPacket.app_file_start_timestamp_machine, data))
    print(timestamps)
    timestamps_np: np.ndarray = np.array(timestamps)
    print(np.diff(timestamps_np))


if __name__ == "__main__":
    main()
