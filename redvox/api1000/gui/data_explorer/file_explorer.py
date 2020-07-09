from datetime import datetime
from glob import glob
import os.path
from pathlib import Path
from typing import List, Optional

from PySide2.QtCore import Slot
from PySide2.QtGui import QFont
from PySide2.QtWidgets import QAbstractItemView, QTreeWidgetItem, QTreeWidget, QWidget
from dataclasses import dataclass
from functools import total_ordering

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

    def __eq__(self, other) -> bool:
        return self.date == other.date

    def __lt__(self, other: 'RdvxmFile') -> bool:
        return self.date < other.date


def find_rdvxm_files(base_dir: str, structured: bool = False) -> List[RdvxmFile]:
    if structured:
        raise RuntimeError("Structured layout is not yet implemented")

    paths: List[str] = glob(os.path.join(base_dir, "*.rdvxm"))
    return sorted(list(map(RdvxmFile.from_path, paths)))


class FileExplorer(QTreeWidget):
    def __init__(self, base_dir: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setColumnCount(3)
        self.setHeaderLabels([
            "Path",
            "Station",
            "Date"
        ])
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        # self.setFont(QFont("Courier"))

        self.rdvxm_files: List[RdvxmFile] = find_rdvxm_files(base_dir)

        for i, rdvxm_file in enumerate(self.rdvxm_files):
            self.insertTopLevelItem(i, QTreeWidgetItem([
                rdvxm_file.filename(),
                rdvxm_file.station_id,
                str(rdvxm_file.date)
            ]))

        self.resizeColumnToContents(0)
        self.resizeColumnToContents(1)

        self.itemSelectionChanged.connect(self.file_selected)

    @Slot()
    def file_selected(self):
        idx: int = self.selectedIndexes()[0].row()
        packet = self.rdvxm_files[idx].read()
        self.parentWidget().packet_explorer.update_from_packet(packet)
        # self.parentWidget().parentWidget().details_column.values_widget.update_with_values(list(packet.get_sensors().get_audio().get_samples().get_values()))
