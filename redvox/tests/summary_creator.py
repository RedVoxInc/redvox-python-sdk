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
from redvox.common.api_reader import ApiReader
from redvox.common.parallel_utils import maybe_parallel_map
from redvox.common.packet_to_pyarrow import AggregateSummary, stream_to_pyarrow, PyarrowSummary
from redvox.common.timesync import TimeSync
from redvox.common.sensor_data import SensorType
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


class ApiReaderSummary(ApiReader):
    def __init__(self,
                 event_name: str,
                 base_dir: str,
                 structured_dir: bool = False,
                 read_filter: io.ReadFilter = None,
                 correct_timestamps: bool = False,
                 use_model_correction: bool = True,
                 arrow_dir: str = ".",
                 debug: bool = False,
                 pool: Optional[multiprocessing.pool.Pool] = None):
        """
        initialize API reader for summaries

        :param event_name: name of the summary to create
        :param base_dir: directory containing the files to read
        :param structured_dir: if True, base_dir contains a specific directory structure used by the respective
                                api formats.  If False, base_dir only has the data files.  Default False.
        :param read_filter: ReadFilter for the data files, if None, get everything.  Default None
        :param correct_timestamps: if True, correct the timestamps of the data.  Default False
        :param use_model_correction: if True, use the offset model of the station to correct the timestamps.
                                        if correct_timestamps is False, this value doesn't matter.  Default True
        :param arrow_dir: the base directory to save parquet files to.  default "." (current directory)
        :param debug: if True, output program warnings/errors during function execution.  Default False.
        """
        super().__init__(base_dir, structured_dir, read_filter, debug, pool)
        self.correct_timestamps = correct_timestamps
        self.use_model_correction = use_model_correction
        self.arrow_dir = os.path.join(arrow_dir, event_name)
        os.makedirs(self.arrow_dir, exist_ok=True)
        self.timesync = TimeSync(arrow_dir=os.path.join(self.arrow_dir, "timesync"))
        os.makedirs(self.timesync.arrow_dir, exist_ok=True)
        self.all_files_size = np.sum([idx.files_size() for idx in self.files_index])
        self.summary = self._read_data()

    def to_dict(self) -> dict:
        """
        :return: the metadata as a dictionary
        """
        return {"timesync": self.timesync.as_dict(),
                "summary": self.summary.to_dict()}

    def to_json(self):
        return json.dumps(self.to_dict())

    def _data_by_index(self, findex: io.Index) -> AggregateSummary:
        """
        builds station using the index of files to read
        splits the index into smaller chunks if entire record cannot be held in memory

        :param findex: index with files to build a station with
        :return: Station built from files in findex, without building the data from parquet
        """
        split_list = self._split_workload(findex)
        result = AggregateSummary()
        if len(split_list) > 0:
            for idx in split_list:
                pkts = idx.read_contents()
                self.timesync.append_timesync_arrow(TimeSync().from_raw_packets(pkts))
                result.add_aggregate_summary(stream_to_pyarrow(pkts, self.arrow_dir), False)
            if self.debug:
                print(f"files read: {len(findex.entries)}")
                if len(split_list) > 1:
                    print(f"required making {len(split_list)} smaller segments due to memory restraints")
            self.timesync.to_json_file()
        else:
            self.errors.append("No files found to create summary.")
        return result

    def _read_data(self, pool: Optional[multiprocessing.pool.Pool] = None) -> AggregateSummary:
        """
        :param pool: optional multiprocessing pool
        :return: List of summaries of data in the ApiReader
        """
        result = AggregateSummary()
        if settings.is_parallelism_enabled() and len(self.files_index) > 1:
            summaries = list(maybe_parallel_map(pool, self._data_by_index,
                                                self.files_index,
                                                chunk_size=1
                                                ))
        else:
            summaries = list(map(self._data_by_index, self.files_index))
        sensors = []
        audio_summaries = []
        for smry in summaries:
            for mry in smry.summaries:
                if mry.stype == SensorType.AUDIO:
                    audio_summaries.append(mry)
                elif mry.stype not in sensors:
                    sensors.append(mry.stype)
        for sensr in sensors:
            result.add_summary(self.merge_summaries(sensr, summaries))
        result.summaries.extend(audio_summaries)
        return result

    def merge_audio_summaries(self):
        """
        combines all audio summaries into a single table and summary, with gaps
        """
        pckt_info = []
        audio_lst = self.summary.get_audio()
        frst_audio = audio_lst[0]
        for adl in audio_lst:
            pckt_info.append((int(adl.start), pq.read_table(adl.file_name())))

        tbl = gpu.fill_audio_gaps2(pckt_info,
                                   dtu.seconds_to_microseconds(1 / frst_audio.srate_hz)
                                   ).create_timestamps()

        frst_audio = PyarrowSummary(frst_audio.name, frst_audio.stype, frst_audio.start, frst_audio.srate_hz,
                                    frst_audio.fdir, tbl.num_rows, frst_audio.smint_s, frst_audio.sstd_s,
                                    tbl)
        frst_audio.write_data(True)

        self.summary.summaries = [sm for sm in self.summary.summaries if sm.stype != SensorType.AUDIO]

        self.summary.add_summary(frst_audio)

    @staticmethod
    def merge_summaries(stype: SensorType, summaries: List[AggregateSummary]) -> PyarrowSummary:
        """
        combines multiple summaries of one sensor into a single one

        *caution: using this on an audio sensor may cause data validation issues*

        :param stype: the type of sensor to combine
        :param summaries: the summaries to look through
        """
        smrs = []
        for smry in summaries:
            for mry in smry.summaries:
                if mry.stype == stype:
                    smrs.append(mry)
        first_summary = smrs.pop(0)
        tbl = first_summary.data()
        for smrys in smrs:
            tbl = pa.concat_tables([first_summary.data(), smrys.data()])
            if first_summary.check_data():
                first_summary._data = tbl
            else:
                os.makedirs(first_summary.fdir, exist_ok=True)
                pq.write_table(tbl, first_summary.file_name())
                os.remove(smrys.file_name())
        mnint = dtu.microseconds_to_seconds(float(np.mean(np.diff(tbl["timestamps"].to_numpy()))))
        stdint = dtu.microseconds_to_seconds(float(np.std(np.diff(tbl["timestamps"].to_numpy()))))
        return PyarrowSummary(first_summary.name, first_summary.stype, first_summary.start,
                              1 / mnint, first_summary.fdir, tbl.num_rows, mnint, stdint,
                              first_summary.data() if first_summary.check_data() else None
                              )


class SensorSummary:
    """
    Summary of a sensor.  contains data about the mean, std and diff of windows of data at a defined interval,
    as well as counts of the enumerated fields
    """
    def __init__(self, interval: float, sensor_name: str, sensor_rate_hz: float,
                 means_data, counts_data: dict, outfile_dir: str):
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


def calc_summary(dur_s: float, snsr: PyarrowSummary, snsr_name: str, tims: TimeSync) -> SensorSummary:
    """
    :param dur_s: duration of a single window of the summary
    :param snsr: a PyarrowSummary with metadata and data for the sensor
    :param snsr_name: the name of the sensor used when saving the SensorSummary
    :param tims: TimeSync for tracking corrections and sensor duration
    :return: a summary of data points per window of the data
    """
    duration_us = dtu.seconds_to_microseconds(dur_s)
    current = tims.data_start_timestamp()
    total_duration = int(dtu.microseconds_to_seconds(tims.data_end_timestamp() - tims.data_start_timestamp()))
    iters = int(total_duration / dur_s)

    tbl = snsr.data()

    prev_mean = np.nan
    print(f"start {snsr_name} summary")
    num_points_per_dur = 1.0 if iters >= tbl.num_rows else tbl.num_rows / iters
    if not(-1 < num_points_per_dur * iters / snsr.srate_hz - total_duration < 1):
        print("Sensor's sample rate * data duration is not consistent with "
              "number of data points per interval * number of summary intervals")
    cur_index = 0

    st = timeit.default_timer()

    channel_names = SENSOR_CHANNEL_NAMES[snsr.stype]

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

    return SensorSummary(dur_s, snsr_name, snsr.srate_hz, pa.Table.from_pydict(means_stds),
                         enum_value_counts, out_dir)


if __name__ == "__main__":
    mydir = "/Users/tyler/Documents/big_data_file_read"
    out_dir = "/Users/tyler/Documents/big_data_file_read/summary"
    ev_name = "big_data_test_run"

    os.chdir(out_dir)

    # s = timeit.default_timer()
    # ar = ApiReaderSummary(event_name=ev_name, base_dir=mydir, arrow_dir=".",
    #                       structured_dir=True, debug=True)
    # e = timeit.default_timer()
    #
    # ar.errors.print()
    # print(f"make stations: {e-s} seconds")
    #
    # ar.merge_audio_summaries()
    #
    # with open(os.path.join(out_dir, f"{ev_name}.json"), 'w') as f:
    #     f.write(ar.to_json())
    # sumries = ar.summary
    #
    # total_size = 0
    # for pth, drnm, flnm in os.walk(out_dir):
    #     for f in flnm:
    #         fp = os.path.join(pth, f)
    #         if not os.path.islink(fp):
    #             total_size += os.path.getsize(fp)
    # print(f"data size: {total_size} B")
    #
    # print("\n**************************************\n")

    duration_s = 1.
    timsnc = TimeSync.from_json_file(os.path.join(out_dir, ev_name, "timesync/timesync.json"))

    with open(f"{ev_name}.json", 'r') as f:
        ar_smry = json.loads(f.read())
    sumries = AggregateSummary.from_dict(ar_smry["summary"])

    audio_summary = calc_summary(duration_s, sumries.get_audio()[0], "microphone", timsnc)
    audio_summary.write_summary()
    del audio_summary

    bar_summary = calc_summary(duration_s, sumries.get_sensor(SensorType.PRESSURE)[0], "barometer", timsnc)
    bar_summary.write_summary()
    del bar_summary

    hlt_summary = calc_summary(duration_s, sumries.get_sensor(SensorType.STATION_HEALTH)[0], "health", timsnc)
    hlt_summary.write_summary()
    del hlt_summary

    loc_summary = calc_summary(duration_s, sumries.get_sensor(SensorType.LOCATION)[0], "location", timsnc)
    loc_summary.write_summary()
    del loc_summary

    acc_summary = calc_summary(duration_s, sumries.get_sensor(SensorType.ACCELEROMETER)[0], "accelerometer", timsnc)
    acc_summary.write_summary()
