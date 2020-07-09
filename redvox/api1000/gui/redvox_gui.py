from functools import total_ordering

from PySide2.QtGui import QFont
from dataclasses import dataclass
from datetime import datetime
from glob import glob
import os.path
from pathlib import Path
import sys
from typing import List

from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QTreeWidget, QTreeWidgetItem, \
    QAbstractItemView

from redvox.api1000.common.common import SamplePayload, SummaryStatistics
from redvox.api1000.common.metadata import Metadata
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM


@total_ordering
@dataclass
class RdvxmFile:
    path: str
    station_id: str
    date: datetime

    @staticmethod
    def from_path(path: str) -> 'RdvxmFile':
        filename: str = Path(path).name
        base: str = filename.split(".")[0]
        split_base: List[str] = base.split("_")
        station_id: str = split_base[0]
        ts_us: int = int(split_base[1])
        date: datetime = datetime.utcfromtimestamp(ts_us / 1E6)

        return RdvxmFile(path, station_id, date)

    def filename(self) -> str:
        return Path(self.path).name

    def read(self) -> WrappedRedvoxPacketM:
        return WrappedRedvoxPacketM.from_compressed_path(self.path)

    def __eq__(self, other: 'RdvxmFile') -> bool:
        return self.date == other.date

    def __lt__(self, other: 'RdvxmFile') -> bool:
        return self.date < other.date


def find_rdvxm_files(base_dir: str, structured: bool = False) -> List[RdvxmFile]:
    if structured:
        raise RuntimeError("Structured layout is not yet implemented")

    paths: List[str] = glob(os.path.join(base_dir, "*.rdvxm"))
    return sorted(list(map(RdvxmFile.from_path, paths)))


class FileExplorer(QTreeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setColumnCount(3)
        self.setHeaderLabels([
            "Path",
            "Station",
            "Date"
        ])
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setFont(QFont("Courier"))

        self.rdvxm_files: List[RdvxmFile] = find_rdvxm_files("/home/opq/scrap/api_m")

        for i, rdvxm_file in enumerate(self.rdvxm_files):
            self.insertTopLevelItem(i, QTreeWidgetItem([
                rdvxm_file.filename(),
                rdvxm_file.station_id,
                str(rdvxm_file.date)
            ]))

        self.resizeColumnToContents(0)
        self.resizeColumnToContents(1)

        self.itemSelectionChanged.connect(self.file_selected)

    def file_selected(self):
        idx: int = self.selectedIndexes()[0].row()
        self.parentWidget().packet_explorer.update_from_packet(self.rdvxm_files[idx].read())


def make_metadata_item(metadata: Metadata) -> QTreeWidgetItem:
    metadata_item: QTreeWidgetItem = QTreeWidgetItem(["metadata", f"<cnt {metadata.get_metadata_count()}>"])
    for key, value in metadata.get_metadata().items():
        metadata_item.addChild(QTreeWidgetItem([key, value]))
    return metadata_item


def make_values_item(values: List) -> QTreeWidgetItem:
    values_item: QTreeWidgetItem = QTreeWidgetItem(["values", f"<cnt {len(values)}>"])
    for i, value in enumerate(values):
        values_item.addChild(QTreeWidgetItem([str(i), str(value)]))
    return values_item


def make_sample_payload_item(sample_payload: SamplePayload) -> QTreeWidgetItem:
    sample_payload_item: QTreeWidgetItem = QTreeWidgetItem(["sample_payload"])
    sample_payload_item.addChildren([
        QTreeWidgetItem(["unit", sample_payload.get_unit().name]),
        make_values_item(list(sample_payload.get_values())),
        make_summary_statistics(sample_payload.get_summary_statistics(), "value_statistics"),
        make_metadata_item(sample_payload.get_metadata())
    ])
    return sample_payload_item


def make_summary_statistics(summary_statistics: SummaryStatistics, name: str = "value_statistics") -> QTreeWidgetItem:
    summary_stats_item: QTreeWidgetItem = QTreeWidgetItem([name])
    summary_stats_item.addChildren([
        QTreeWidgetItem(["count", str(summary_statistics.get_count())]),
        QTreeWidgetItem(["mean", str(summary_statistics.get_mean())]),
        QTreeWidgetItem(["median", str(summary_statistics.get_median())]),
        QTreeWidgetItem(["mode", str(summary_statistics.get_mode())]),
        QTreeWidgetItem(["variance", str(summary_statistics.get_variance())]),
        QTreeWidgetItem(["min", str(summary_statistics.get_min())]),
        QTreeWidgetItem(["max", str(summary_statistics.get_max())]),
        QTreeWidgetItem(["range", str(summary_statistics.get_range())]),
        make_metadata_item(summary_statistics.get_metadata())
    ])
    return summary_stats_item


class PacketExplorer(QTreeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setColumnCount(2)
        self.setHeaderLabels([
            "Field",
            "Value"
        ])

    def update_from_packet(self, wrapped_packet: WrappedRedvoxPacketM) -> None:
        self.clear()

        station_info = wrapped_packet.get_station_information()

        app_settings_item: QTreeWidgetItem = QTreeWidgetItem(["app_settings"])
        app_settings = station_info.get_app_settings()
        app_settings_item.addChildren([
            QTreeWidgetItem(["audio_sampling_rate", app_settings.get_audio_sampling_rate().name]),
            QTreeWidgetItem(["audio_source_tuning", app_settings.get_audio_source_tuning().name]),
            QTreeWidgetItem(
                ["additional_input_sensors", str(app_settings.get_additional_input_sensors().get_values())]),
            QTreeWidgetItem(["automatically_record", str(app_settings.get_automatically_record())]),
            QTreeWidgetItem(["launch_at_power_up", str(app_settings.get_launch_at_power_up())]),
            QTreeWidgetItem(["station_id", app_settings.get_station_id()]),
            QTreeWidgetItem(["push_to_server", str(app_settings.get_push_to_server())]),
            QTreeWidgetItem(["publish_data_as_private", str(app_settings.get_publish_data_as_private())]),
            QTreeWidgetItem(["scramble_audio_data", str(app_settings.get_scramble_audio_data())]),
            QTreeWidgetItem(["provide_backfill", str(app_settings.get_provide_backfill())]),
            QTreeWidgetItem(["remove_sensor_dc_offset", str(app_settings.get_remove_sensor_dc_offset())]),
            QTreeWidgetItem(["fft_overlap", str(app_settings.get_fft_overlap())]),
            QTreeWidgetItem(["use_custom_time_sync_server", str(app_settings.get_use_custom_time_sync_server())]),
            QTreeWidgetItem(["time_sync_server_url", app_settings.get_time_sync_server_url()]),
            QTreeWidgetItem(["use_custom_data_server", str(app_settings.get_use_custom_data_server())]),
            QTreeWidgetItem(["data_server_url", app_settings.get_data_server_url()]),
            QTreeWidgetItem(["auto_delete_data_files", str(app_settings.get_auto_delete_data_files())]),
            QTreeWidgetItem(["storage_space_allowance", str(app_settings.get_storage_space_allowance())]),
            QTreeWidgetItem(["use_sd_card_for_data_storage", str(app_settings.get_use_sd_card_for_data_storage())]),
            QTreeWidgetItem(["use_location_services", str(app_settings.get_use_location_services())]),
            QTreeWidgetItem(["use_latitude", str(app_settings.get_use_latitude())]),
            QTreeWidgetItem(["use_longitude", str(app_settings.get_use_longitude())]),
            QTreeWidgetItem(["use_altitude", str(app_settings.get_use_altitude())]),
            make_metadata_item(app_settings.get_metadata()),
        ])

        station_metrics_item: QTreeWidgetItem = QTreeWidgetItem(["station_metrics"])
        station_metrics = station_info.get_station_metrics()
        station_metrics_item.addChildren([

        ])

        service_urls_item: QTreeWidgetItem = QTreeWidgetItem(["service_urls"])
        service_urls = station_info.get_service_urls()
        service_urls_item.addChildren([
            QTreeWidgetItem(["auth_server", service_urls.get_auth_server()]),
            QTreeWidgetItem(["synch_server", service_urls.get_synch_server()]),
            QTreeWidgetItem(["acquisition_server", service_urls.get_acquisition_server()]),
            make_metadata_item(service_urls.get_metadata())
        ])

        station_info_item: QTreeWidgetItem = QTreeWidgetItem(["station_information"])
        station_info_item.addChildren([
            QTreeWidgetItem(["id", station_info.get_id()]),
            QTreeWidgetItem(["uuid", station_info.get_uuid()]),
            QTreeWidgetItem(["auth_id", station_info.get_auth_id()]),
            QTreeWidgetItem(["make", station_info.get_make()]),
            QTreeWidgetItem(["model", station_info.get_model()]),
            QTreeWidgetItem(["os", station_info.get_os().name]),
            QTreeWidgetItem(["os_version", station_info.get_os_version()]),
            QTreeWidgetItem(["app_version", station_info.get_app_version()]),
            QTreeWidgetItem(["is_private", str(station_info.get_is_private())]),
            app_settings_item,
            station_metrics_item,
            service_urls_item,
            make_metadata_item(station_info.get_metadata())
        ])

        timing_info_item: QTreeWidgetItem = QTreeWidgetItem(["timing_information"])
        timing_info = wrapped_packet.get_timing_information()
        synch_exchanges_item: QTreeWidgetItem = QTreeWidgetItem(
            ["synch_exchanges", f"<cnt {timing_info.get_synch_exchanges().get_count()}>"])

        for exchange in timing_info.get_synch_exchanges().get_values():
            synch_exchanges_item.addChildren([
                QTreeWidgetItem(["a1", str(exchange.get_a1())]),
                QTreeWidgetItem(["a2", str(exchange.get_a2())]),
                QTreeWidgetItem(["a3", str(exchange.get_a3())]),
                QTreeWidgetItem(["b1", str(exchange.get_a1())]),
                QTreeWidgetItem(["b2", str(exchange.get_a2())]),
                QTreeWidgetItem(["b3", str(exchange.get_a3())]),
                QTreeWidgetItem(["unit", str(exchange.get_unit())]),
                make_metadata_item(exchange.get_metadata())
            ])

        timing_info_item.addChildren([
            QTreeWidgetItem(["packet_start_os_timestamp", str(timing_info.get_packet_start_os_timestamp())]),
            QTreeWidgetItem(["packet_start_mach_timestamp", str(timing_info.get_packet_start_mach_timestamp())]),
            QTreeWidgetItem(["packet_end_os_timestamp", str(timing_info.get_packet_end_os_timestamp())]),
            QTreeWidgetItem(["packet_end_mach_timestamp", str(timing_info.get_packet_end_mach_timestamp())]),
            QTreeWidgetItem(["server_acquisition_arrival_timestamp",
                             str(timing_info.get_server_acquisition_arrival_timestamp())]),
            QTreeWidgetItem(["app_start_mach_timestamp", str(timing_info.get_app_start_mach_timestamp())]),
            synch_exchanges_item,
            QTreeWidgetItem(["best_latency", str(timing_info.get_best_latency())]),
            QTreeWidgetItem(["best_offset", str(timing_info.get_best_offset())]),
            QTreeWidgetItem(["score", str(timing_info.get_score())]),
            QTreeWidgetItem(["score_method", str(timing_info.get_score_method().name)]),
            QTreeWidgetItem(["unit", str(timing_info.get_unit().name)]),
            make_metadata_item(timing_info.get_metadata()),
        ])

        sensors_item: QTreeWidgetItem = QTreeWidgetItem(["sensors"])
        sensors = wrapped_packet.get_sensors()
        audio_item: QTreeWidgetItem = QTreeWidgetItem(["audio"])
        audio = sensors.get_audio()

        if audio:
            audio_item.addChildren([
                QTreeWidgetItem(["sensor_description", str(audio.get_sensor_description())]),
                QTreeWidgetItem(["first_sample_timestamp", str(audio.get_first_sample_timestamp())]),
                QTreeWidgetItem(["sample_rate", str(audio.get_sample_rate())]),
                QTreeWidgetItem(["bits_of_precision", str(audio.get_bits_of_precision())]),
                QTreeWidgetItem(["is_scrambled", str(audio.get_is_scrambled())]),
                QTreeWidgetItem(["encoding", str(audio.get_encoding())]),
                make_sample_payload_item(audio.get_samples()),
                make_metadata_item(audio.get_metadata()),
            ])

        sensors_item.addChildren([
            QTreeWidgetItem(["accelerometer"]),
            QTreeWidgetItem(["ambient_temperature"]),
            audio_item,
            QTreeWidgetItem(["compressed_audio"]),
            QTreeWidgetItem(["gravity"]),
            QTreeWidgetItem(["gyroscope"]),
            QTreeWidgetItem(["image"]),
            QTreeWidgetItem(["light"]),
            QTreeWidgetItem(["linear_acceleration"]),
            QTreeWidgetItem(["location"]),
            QTreeWidgetItem(["magnetometer"]),
            QTreeWidgetItem(["orientation"]),
            QTreeWidgetItem(["pressure"]),
            QTreeWidgetItem(["proximity"]),
            QTreeWidgetItem(["relative_humidity"]),
            QTreeWidgetItem(["rotation_vector"]),
            make_metadata_item(sensors.get_metadata()),
        ])

        self.insertTopLevelItem(0, QTreeWidgetItem(["api", str(wrapped_packet.get_api())]))
        self.insertTopLevelItem(1, station_info_item)
        self.insertTopLevelItem(2, timing_info_item)
        self.insertTopLevelItem(3, sensors_item)
        self.insertTopLevelItem(4, make_metadata_item(wrapped_packet.get_metadata()))
        self.setHeaderLabels(["Field", "Value"])
        self.setColumnWidth(0, 400)


class DataExplorer(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_explorer: FileExplorer = FileExplorer()
        self.file_explorer.setParent(self)
        self.packet_explorer: PacketExplorer = PacketExplorer()
        self.packet_explorer.setParent(self)

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.file_explorer)
        self.layout().addWidget(self.packet_explorer)
        # self.layout().addWidget(QTreeWidget())


class RedvoxGui(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.data_explorer: DataExplorer = DataExplorer()
        self.data_explorer.setParent(self)

        self.setWindowTitle("RedVox")
        self.setCentralWidget(self.data_explorer)


def main() -> None:
    app: QApplication = QApplication(sys.argv)
    window: RedvoxGui = RedvoxGui()
    window.showMaximized()
    app.exec_()


if __name__ == "__main__":
    main()
