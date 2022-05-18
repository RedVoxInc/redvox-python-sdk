"""
This file is designed to show the usage of the redvox SDK when loading DataWindows from existing files
This file is expected to be in the same directory as the JSON file being loaded,
and there is only one JSON file to load.
This file is expected to work with SDK version 3.1.4 and higher
"""
import redvox.common.data_window as dwa
from redvox.common.io import get_json_file


def main():
    files = get_json_file(".")
    if files is None:
        raise KeyError("Missing .json file to load!")
    dw = dwa.DataWindow.load(f"./{files}")

    print("Stations by ID in Data Window:", [sttn.id() for sttn in dw.stations()])
    st = dw.first_station()

    print(f"Sensors in Station {st.id()}:", st.get_sensors())
    audio = st.audio_sensor()
    print(f"Audio Sensor {audio.name} Data: ", audio.get_microphone_data())

    # use your choice of plotting library to plot the data
    # example using matplotlib:

    # import matplotlib.pyplot as plt
    # print("Plotting data")
    # plt.figure(figsize=(8, 6))
    # plt.plot(audio.data_timestamps() - audio.first_data_timestamp(), audio.get_microphone_data())
    # plt.ylabel("Audio")
    # plt.xlabel("Time")
    # plt.title("Audio Data")
    # plt.show()


if __name__ == "__main__":
    main()
