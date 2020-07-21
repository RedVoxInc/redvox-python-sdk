from datetime import datetime
from typing import List, Optional

from PySide2.QtWidgets import QTreeWidgetItem, QTreeWidget, QWidget

from redvox.api1000.common.common import SamplePayload, SummaryStatistics
from redvox.api1000.common.metadata import Metadata
from redvox.api1000.gui.data_explorer.packet_details import DateTimes
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM


def make_metadata_item(metadata: Metadata) -> QTreeWidgetItem:
    metadata_item: QTreeWidgetItem = QTreeWidgetItem(["metadata", f"<cnt {metadata.get_metadata_count()}>"])
    for key, value in metadata.get_metadata().items():
        metadata_item.addChild(QTreeWidgetItem([key, value]))
    return metadata_item


def make_summary_statistics(summary_statistics: SummaryStatistics, name: str = "value_statistics") -> QTreeWidgetItem:
    summary_stats_item: QTreeWidgetItem = QTreeWidgetItem([name])
    summary_stats_item.addChildren([
        QTreeWidgetItem(["count", str(summary_statistics.get_count())]),
        QTreeWidgetItem(["mean", str(summary_statistics.get_mean())]),
        QTreeWidgetItem(["standard_deviation", str(summary_statistics.get_standard_deviation())]),
        QTreeWidgetItem(["min", str(summary_statistics.get_min())]),
        QTreeWidgetItem(["max", str(summary_statistics.get_max())]),
        QTreeWidgetItem(["range", str(summary_statistics.get_range())]),
        make_metadata_item(summary_statistics.get_metadata())
    ])
    return summary_stats_item


class PacketExplorer(QTreeWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHeaderLabels([
            "Field",
            "Value"
        ])

        self.wrapped_packet: Optional[WrappedRedvoxPacketM] = None

    def make_values_item(self, values_type: str, values_cnt: int) -> QTreeWidgetItem:
        values_item: QTreeWidgetItem = QTreeWidgetItem([f"<{values_type} values>", f"<cnt {values_cnt}>"])
        return values_item

    def make_sample_payload_item(self, sensor_type: str, sample_payload: SamplePayload) -> QTreeWidgetItem:
        sample_payload_item: QTreeWidgetItem = QTreeWidgetItem([f"<{sensor_type}> sample_payload"])
        sample_payload_item.addChildren([
            QTreeWidgetItem(["unit", sample_payload.get_unit().name]),
            self.make_values_item(sensor_type, sample_payload.get_values_count()),
            make_summary_statistics(sample_payload.get_summary_statistics(), "value_statistics"),
            make_metadata_item(sample_payload.get_metadata())
        ])
        return sample_payload_item

    def check_if_value_item(self, current: QTreeWidgetItem, previous: Optional[QTreeWidgetItem]):
        text: str = current.text(0)
        if " values>" in text:
            values: List[float] = []
            if text == "<audio values>":
                audio = self.wrapped_packet.get_sensors().get_audio()
                values = list(audio.get_samples().get_values())
                dts = DateTimes.from_sr(audio.get_first_sample_timestamp(),
                                        audio.get_sample_rate(),
                                        audio.get_samples().get_values_count())
                self.parentWidget().parentWidget().details_column.values_widget.update_from_values(values, dts)
                self.parentWidget().parentWidget().details_column.plot_widget.update_from_values(values, dts)

    def update_from_packet(self, wrapped_packet: WrappedRedvoxPacketM) -> None:
        self.wrapped_packet = wrapped_packet
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
            QTreeWidgetItem(["fft_overlap", str(app_settings.get_fft_overlap().name)]),
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
            self.make_sample_payload_item("network_strength", station_metrics.get_network_strength()),
            self.make_sample_payload_item("temperature", station_metrics.get_temperature()),
            self.make_sample_payload_item("battery", station_metrics.get_battery()),
            self.make_sample_payload_item("battery_current", station_metrics.get_battery_current()),
            self.make_sample_payload_item("available_ram", station_metrics.get_available_ram()),
            self.make_sample_payload_item("available_disk", station_metrics.get_available_disk()),
            self.make_sample_payload_item("cpu_utilization", station_metrics.get_cpu_utilization()),
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
            QTreeWidgetItem(["description", station_info.get_description()]),
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
                self.make_sample_payload_item("audio", audio.get_samples()),
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

        self.currentItemChanged.connect(self.check_if_value_item)

        self.insertTopLevelItem(0, QTreeWidgetItem(["api", str(wrapped_packet.get_api())]))
        self.insertTopLevelItem(1, station_info_item)
        self.insertTopLevelItem(2, timing_info_item)
        self.insertTopLevelItem(3, sensors_item)
        self.insertTopLevelItem(4, make_metadata_item(wrapped_packet.get_metadata()))
        self.setHeaderLabels(["Field", "Value"])
        self.setColumnWidth(0, 400)
