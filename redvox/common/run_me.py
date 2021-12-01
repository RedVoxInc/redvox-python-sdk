from glob import glob

import matplotlib.pyplot as plt
import redvox.common.data_window as dwa


def main():
    files = glob("./*.json")
    if len(files) < 1:
        raise KeyError("Missing .json file to load!")
    dw = dwa.DataWindow.load(files[0])

    print("Stations in Data Window:", dw.stations())
    st = dw.first_station()

    print(f"Sensors in Station {st.id()}:", st.get_sensors())
    audio = st.audio_sensor()
    print(f"Audio Sensor {audio.name} Data: ", audio.get_microphone_data())

    print("Plotting data")
    plt.figure(figsize=(8, 6))
    plt.plot(audio.data_timestamps() - audio.first_data_timestamp(), audio.get_microphone_data())
    plt.ylabel("Audio")
    plt.xlabel("Time")
    plt.title("Audio Data")
    plt.show()


if __name__ == "__main__":
    main()
