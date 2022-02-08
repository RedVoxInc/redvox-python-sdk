"""
Testing DataWindowArrow
"""
import os.path
import timeit
from typing import List, Optional

import json
import multiprocessing.pool
import numpy as np
import pyarrow.parquet as pq
import pyarrow as pa

from redvox.common import io
from redvox.common import date_time_utils as dtu
from redvox.common.api_reader_dw import ApiReaderDw
from redvox.common.parallel_utils import maybe_parallel_map
from redvox.common.packet_to_pyarrow import AggregateSummary, stream_to_pyarrow, PyarrowSummary
from redvox.common.timesync import TimeSync
from redvox.common.sensor_data import SensorType
from redvox.common.io import FileSystemSaveMode
from redvox.common.station import Station
import redvox.common.gap_and_pad_utils as gpu
import redvox.settings as settings
from redvox.api1000.wrapped_redvox_packet.station_information import (
    NetworkType,
    PowerState,
    CellServiceState,
    WifiWakeLock,
    ScreenState,
)
from redvox.api1000.wrapped_redvox_packet.sensors.location import LocationProvider

settings.set_parallelism_enabled(False)


SENSOR_CHANNEL_NAMES = {
    SensorType.AUDIO: ["microphone"],
    SensorType.PRESSURE: ["pressure"],
    SensorType.LOCATION: ["gps_timestamps",
                          "latitude",
                          "longitude",
                          "altitude",
                          "speed",
                          "bearing",
                          "horizontal_accuracy",
                          "vertical_accuracy",
                          "speed_accuracy",
                          "bearing_accuracy",
                          "location_provider"],
    SensorType.BEST_LOCATION: ["gps_timestamps",
                               "latitude",
                               "longitude",
                               "altitude",
                               "speed",
                               "bearing",
                               "horizontal_accuracy",
                               "vertical_accuracy",
                               "speed_accuracy",
                               "bearing_accuracy",
                               "location_provider"],
    SensorType.ACCELEROMETER: ["accelerometer_x",
                               "accelerometer_y",
                               "accelerometer_z"],
    SensorType.GYROSCOPE: ["gyroscope_x",
                           "gyroscope_y",
                           "gyroscope_z"],
    SensorType.MAGNETOMETER: ["magnetometer_x",
                              "magnetometer_y",
                              "magnetometer_z"],
    SensorType.STATION_HEALTH: ["battery_charge_remaining",
                                "battery_current_strength",
                                "internal_temp_c",
                                "network_type",
                                "network_strength",
                                "power_state",
                                "avail_ram",
                                "avail_disk",
                                "cell_service",
                                "cpu_utilization",
                                "wifi_wake_lock",
                                "screen_state",
                                "screen_brightness"],
    SensorType.IMAGE: ["image"],
    SensorType.PROXIMITY: ["proximity"],
    SensorType.LIGHT: ["light"],
    SensorType.COMPRESSED_AUDIO: [],
    SensorType.AMBIENT_TEMPERATURE: ["ambient_temperature"],
    SensorType.RELATIVE_HUMIDITY: ["relative_humidity"],
    SensorType.GRAVITY: ["gravity_x",
                         "gravity_y",
                         "gravity_z"],
    SensorType.ORIENTATION: ["orientation_x",
                             "orientation_y",
                             "orientation_z"],
    SensorType.LINEAR_ACCELERATION: ["linear_acceleration_x",
                                     "linear_acceleration_y",
                                     "linear_acceleration_z"],
    SensorType.ROTATION_VECTOR: ["rotation_vector_x",
                                 "rotation_vector_y",
                                 "rotation_vector_z"]
}

ENUMERATED_CHANNEL_NAMES = {"location_provider": [e.value for e in LocationProvider],
                            "network_type": [e.value for e in NetworkType],
                            "power_state": [e.value for e in PowerState],
                            "cell_service": [e.value for e in CellServiceState],
                            "wifi_wake_lock": [e.value for e in WifiWakeLock],
                            "screen_state": [e.value for e in ScreenState]}

DIFF_ONLY_CHANNEL_NAMES = ["image"]

ENUMERATED_CHANNEL_TO_ENUMERATION = {"location_provider": [e.name for e in LocationProvider],
                                     "network_type": [e.name for e in NetworkType],
                                     "power_state": [e.name for e in PowerState],
                                     "cell_service": [e.name for e in CellServiceState],
                                     "wifi_wake_lock": [e.name for e in WifiWakeLock],
                                     "screen_state": [e.name for e in ScreenState]}


class SensorSummary:
    """
    Summary of a sensor.  contains data about the mean, std and diff of windows of data at a defined interval,
    as well as counts of the enumerated fields
    """
    def __init__(self, interval: float, sensor_name: str, sensor_rate_hz: float,
                 means_data: pa.Table, counts_data: dict, outfile_dir: str):
        self.interval = interval
        self.sensor_name = sensor_name
        self.sensor_rate_hz = sensor_rate_hz
        self.means_data = means_data
        self.out_dir = outfile_dir

        self.counts_data = {}
        for ev in counts_data:
            self.counts_data[ev] = {}
            for rv in counts_data[ev].keys():
                self.counts_data[ev][ENUMERATED_CHANNEL_TO_ENUMERATION[ev][int(rv)]] = counts_data[ev][rv]

    def as_dict(self) -> dict:
        return {"sensor_name": self.sensor_name,
                "sensor_rate_hz": self.sensor_rate_hz,
                "summary_interval": self.interval,
                "points_per_interval": self.interval*self.sensor_rate_hz,
                "counts_data": self.counts_data}

    def as_json(self) -> str:
        return json.dumps(self.as_dict())

    def write_summary(self):
        summary_path = os.path.join(self.out_dir, "summaries")
        os.makedirs(summary_path, exist_ok=True)
        with open(os.path.join(summary_path, f"{self.sensor_name}.json"), "w") as fl:
            fl.write(self.as_json())
        pq.write_table(self.means_data, os.path.join(summary_path, f"{self.sensor_name}.parquet"))


def calc_summary(dur_s: float, station: Station, stype: SensorType, snsr_name: str,
                 out_dr: Optional[str] = None) -> SensorSummary:
    """
    :param dur_s: duration in seconds of a single window of the summary
    :param station: the Station that contains the data to create a summary
    :param stype: the type of sensor to create a summary for
    :param snsr_name: the name of the sensor used when saving the SensorSummary
    :param out_dr: optional output directory for the summary; defaults to station's save directory
    :return: a summary of data points per window of the data
    """
    duration_us = dtu.seconds_to_microseconds(dur_s)
    current = station.timesync_data().data_start_timestamp()
    total_duration = int(dtu.microseconds_to_seconds(
        station.timesync_data().data_end_timestamp() - station.timesync_data().data_start_timestamp()))
    iters = int(total_duration / dur_s)

    tbl = station.get_sensor_by_type(stype).pyarrow_table()

    prev_mean = np.nan
    print(f"start {snsr_name} summary")
    num_points_per_dur = 1.0 if iters >= tbl.num_rows else tbl.num_rows / iters
    if not(-1 < num_points_per_dur * iters / station.get_sensor_by_type(stype).sample_rate_hz() - total_duration < 1):
        print("Sensor's sample rate * data duration is not consistent with "
              "number of data points per interval * number of summary intervals")
    cur_index = 0

    st = timeit.default_timer()

    channel_names = SENSOR_CHANNEL_NAMES[stype]

    means_stds: dict = {"timestamp": []}
    enum_value_counts: dict = {}
    for cn in channel_names:
        if cn in ENUMERATED_CHANNEL_NAMES.keys():
            enum_value_counts[f"{cn}"] = {}
            for ev in ENUMERATED_CHANNEL_NAMES[cn]:
                enum_value_counts[f"{cn}"][ev] = 0
        else:
            means_stds[f"{cn}_mean"] = []
            means_stds[f"{cn}_std"] = []
            means_stds[f"{cn}_diff"] = []

    for i in range(iters):
        means_stds["timestamp"].append(current)
        slce = tbl.slice(int(cur_index), int(num_points_per_dur))
        for cn in channel_names:
            if cn in DIFF_ONLY_CHANNEL_NAMES:
                if len(slce) < 1:
                    print("HOI!  EMPTY SLICE AT: ", current)
                else:
                    if np.isnan(prev_mean):
                        prev_mean = np.full(len(slce[cn]), np.nan)
                        # todo images all better be the same length
                    mean = np.mean([slce[cn].to_pylist(), prev_mean], axis=0)
                    means_stds[f"{cn}_mean"].append(mean)
                    means_stds[f"{cn}_std"].append(np.std([slce[cn].to_pylist(), prev_mean], axis=0))
                    means_stds[f"{cn}_diff"].append(mean - prev_mean)
                    prev_mean = mean
            elif cn in ENUMERATED_CHANNEL_NAMES.keys():
                for v in slce[cn].to_pylist():
                    enum_value_counts[cn][v] = enum_value_counts[cn][v] + 1
            elif len(slce) < 1:
                print(f"EMPTY SLICE IN {cn} AT: {current}")
                means_stds[f"{cn}_mean"].append(np.nan)
                means_stds[f"{cn}_std"].append(0.)
                means_stds[f"{cn}_diff"].append(np.nan)
            else:
                mean = np.mean(slce[cn].to_numpy())
                means_stds[f"{cn}_mean"].append(mean)
                means_stds[f"{cn}_std"].append(np.std(slce[cn].to_numpy()))
                means_stds[f"{cn}_diff"].append(mean - prev_mean)
                prev_mean = mean
        current += duration_us
        cur_index += num_points_per_dur

    en = timeit.default_timer()
    print(f"{snsr_name} summary grind: {en-st} seconds")

    return SensorSummary(dur_s, snsr_name, station.get_sensor_by_type(stype).sample_rate_hz(),
                         pa.Table.from_pydict(means_stds), enum_value_counts,
                         out_dr if out_dr is None else station.save_dir())


if __name__ == "__main__":
    mydir = "/Users/tyler/Documents/big_data_file_read"
    out_dir = "/Users/tyler/Documents/big_data_file_read/summary"
    ev_name = "big_data_test_run"
    smry_out_dir = os.path.join(out_dir, "summaries")

    os.chdir(out_dir)

    # s = timeit.default_timer()
    # ar = ApiReaderDw(base_dir=mydir, structured_dir=True, debug=True,
    #                  dw_base_dir=".", save_mode=FileSystemSaveMode.DISK)
    # stations = ar.get_stations()
    # e = timeit.default_timer()
    #
    # ar.errors.print()
    # print(f"make stations: {e-s} seconds")
    #
    # for stn in stations:
    #     stn.save()

    sttn = Station.load(os.path.join(out_dir, '1637620005_1641846545849000'))

    total_size = 0
    for pth, drnm, flnm in os.walk(sttn.save_dir()):
        for f in flnm:
            fp = os.path.join(pth, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    print(f"data size: {total_size} B")

    print("\n**************************************\n")

    duration_s = 1.

    audio_summary = calc_summary(duration_s, sttn, SensorType.AUDIO, "microphone", smry_out_dir)
    audio_summary.write_summary()
    del audio_summary

    bar_summary = calc_summary(duration_s, sttn, SensorType.PRESSURE, "barometer", smry_out_dir)
    bar_summary.write_summary()
    del bar_summary

    hlt_summary = calc_summary(duration_s, sttn, SensorType.STATION_HEALTH, "health", smry_out_dir)
    hlt_summary.write_summary()
    del hlt_summary

    loc_summary = calc_summary(duration_s, sttn, SensorType.LOCATION, "location", smry_out_dir)
    loc_summary.write_summary()
    del loc_summary

    acc_summary = calc_summary(duration_s, sttn, SensorType.ACCELEROMETER, "accelerometer", smry_out_dir)
    acc_summary.write_summary()
