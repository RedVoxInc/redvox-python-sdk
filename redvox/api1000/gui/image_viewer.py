import sys
from dataclasses import dataclass
import datetime
from typing import Dict, List, Optional

import numpy as np
from PySide2.QtCore import QStringListModel
from PySide2.QtGui import QStandardItemModel, QStandardItem
from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QLabel, QListView, QTableView, QSplitter, \
    QListWidget, QTableWidget, QTableWidgetItem, QHeaderView

import redvox
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.api1000.wrapped_redvox_packet.sensors.image import Image


class ImageViewer(QWidget):
    def __init__(self, image_sensor: Image, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setLayout(QHBoxLayout(self))

        ext: str = image_sensor.get_file_ext()
        tss: np.ndarray = image_sensor.get_timestamps().get_timestamps()

        image_list: QTableWidget = QTableWidget(image_sensor.get_num_images(), 2, self)
        image_list.setHorizontalHeaderLabels(["File Name", "Image Taken"])
        image_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for (i, ts) in enumerate(tss):
            name: str = f"{round(ts)}.{ext}"
            dt: datetime.datetime = datetime.datetime.utcfromtimestamp(ts / 1_000_000.0)
            image_list.setItem(i, 0, QTableWidgetItem(name))
            image_list.setItem(i, 1, QTableWidgetItem(str(dt)))

        self.layout().addWidget(image_list)
        self.layout().addWidget(QLabel("bar"))


class MainWindow(QMainWindow):
    def __init__(self, image_sensor: Image, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"RedVox Image Viewer v{redvox.VERSION}")
        self.setCentralWidget(ImageViewer(image_sensor, self))


def start_gui(image_sensor: Image) -> None:
    app: QApplication = QApplication(sys.argv)
    window: MainWindow = MainWindow(image_sensor)
    window.showMaximized()
    app.exec_()


if __name__ == "__main__":
    path = "/home/opq/data/api_m_image/1637680002_1600191160612108.rdvxm"
    packet = WrappedRedvoxPacketM.from_compressed_path(path)
    start_gui(packet.get_sensors().get_image())
