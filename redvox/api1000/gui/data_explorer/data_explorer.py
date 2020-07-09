from typing import Optional

from PySide2.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget

from redvox.api1000.gui.data_explorer.file_explorer import FileExplorer
from redvox.api1000.gui.data_explorer.packet_details import PlotAndDetailsColumn
from redvox.api1000.gui.data_explorer.packet_explorer import PacketExplorer


class FileAndPacketExplorerColumn(QWidget):
    def __init__(self, base_dir: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.file_explorer: FileExplorer = FileExplorer(base_dir, self)
        self.packet_explorer: PacketExplorer = PacketExplorer(self)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.file_explorer)
        self.layout().addWidget(self.packet_explorer)


class DataExplorer(QWidget):
    def __init__(self, base_dir: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.explorer_column = FileAndPacketExplorerColumn(base_dir, self)
        self.details_column = PlotAndDetailsColumn(self)

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.explorer_column)
        self.layout().addWidget(self.details_column)
